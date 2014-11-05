import numpy as np
import pygame
import sys

from random import randrange

def execute_opcode(opcode):
    global pc, I, V, stack, sp, memory, screen, delay_timer, sound_timer
    case1 = opcode & 0xF000

    if case1 == 0x0000:
        if opcode == 0x00E0:
            # 00E0: Clears the screen
            screen.surface.fill((0, 0, 0))
        elif opcode == 0x00EE:
            # 00EE: Returns from a subroutine
            sp -= 1
            pc = stack[sp]
        else:
            # 0NNN: Calls program at address NNN
            #print("0NNN Call")
            pass
    elif case1 == 0x1000:
        # 1NNN: Jumps to address NNN
        pc = opcode & 0x0FFF
        # Decrement the pc to undo the automatic increment after each opcode
        pc -= 2
    elif case1 == 0x2000:
        # 2NNN: Calls subroutine at NNN
        stack[sp] = pc
        sp += 1
        pc = opcode & 0x0FFF
        pc -= 2
    elif case1 == 0x3000:
        # 3XNN: Skips the next instruction if VX equals NN
        if V[(opcode & 0x0F00) >> 8] == opcode & 0x00FF:
            pc += 2
    elif case1 == 0x4000:
        # 4XNN: Skips the next instruction if VX doesn't equal NN
        if V[(opcode & 0x0F00) >> 8] != opcode & 0x00FF:
            pc += 2
    elif case1 == 0x5000:
        # 5XY0: Skips the next instruction if VX equals VY
        if V[(opcode & 0x0F00) >> 8] == opcode & V[(opcode & 0x00F0) >> 4]:
            pc += 2
    elif case1 == 0x6000:
        # 6XNN: Sets VX to NN
        V[(opcode & 0x0F00) >> 8] = opcode & 0x00FF
    elif case1 == 0x7000:
        # 7XNN: Adds NN to VX
        result = V[(opcode & 0x0F00) >> 8] + opcode & 0x00FF
        V[(opcode & 0x0F00) >> 8] = result
        if result > 255:
            V[0xF] = 1
        else:
            V[0xF] = 0

    elif case1 == 0x8000:
        case2 = opcode & 0x000F
        if case2 == 0x0:
            # 8XY0: Sets VX to the value of VY
            V[(opcode & 0x0F00) >> 8] = V[(opcode & 0x00F0) >> 4]
        elif case2 == 0x1:
            # 8XY1: Sets VX to the value of VX OR VY
            V[(opcode & 0x0F00) >> 8] = V[(opcode & 0x0F00) >> 8] | V[(opcode & 0x00F0) >> 4]
        elif case2 == 0x2:
            # 8XY2: Sets VX to the value of VX AND VY
            V[(opcode & 0x0F00) >> 8] = V[(opcode & 0x0F00) >> 8] & V[(opcode & 0x00F0) >> 4]
        elif case2 == 0x3:
            # 8XY3: Sets VX to the value of VX XOR VY
            V[(opcode & 0x0F00) >> 8] = V[(opcode & 0x0F00) >> 8] ^ V[(opcode & 0x00F0) >> 4]
        elif case2 == 0x4:
            # 8XY4: Adds VY to VX, VF is 1 when there is a carry, else 0
            result = int(V[(opcode & 0x0F00) >> 8]) + int(V[(opcode & 0x00F0) >> 4])
            print(V[(opcode & 0x0F00) >> 8], V[(opcode & 0x00F0) >> 4], result)
            V[(opcode & 0x0F00) >> 8] = result
            if result > 255:
                V[0xF] = 1
            else:
                V[0xF] = 0
        elif case2 == 0x5:
            # 8XY5: VY is subtracted from VX, VF is 0 when there is a borrow, else 1
            result = int(V[(opcode & 0x0F00) >> 8]) - int(V[(opcode & 0x00F0) >> 4])
            V[(opcode & 0x0F00) >> 8] = result
            if result < 0:
                V[0xF] = 0
            else:
                V[0xF] = 1
        elif case2 == 0x6:
            # 8XY6: Shifts VX right by 1, VF is set to LSB before shift
            V[0xF] = V[(opcode & 0x0F00) >> 8] & 0x1
            V[(opcode & 0x0F00) >> 8] >>= 1
        elif case2 == 0x7:
            # 8XY7: Sets VX to VY minus VX, VF is 0 when there is a borrow, else 1
            result = int(V[(opcode & 0x00F0) >> 4]) - int(V[(opcode & 0x0F00) >> 8])
            V[(opcode & 0x0F00) >> 8] = result
            if result < 0:
                V[0xF] = 0
            else:
                V[0xF] = 1
        elif case2 == 0xE:
            # 8XYE: Shifts VX left by 1, VF is set to MSB before shift
            V[0xF] = (V[(opcode & 0x0F00) >> 8] & 0x80) >> 7
            V[(opcode & 0x0F00) >> 8] <<= 1
    elif case1 == 0x9000:
        # 9XY0: Skips next instruction if VX is not equal to VY
        if V[(opcode & 0x0F00) >> 8] != V[(opcode & 0x00F0) >> 4]:
            pc += 2
    elif case1 == 0xA000:
        # ANNN: Set register I to NNN
        I = opcode & 0x0FFF
    elif case1 == 0xB000:
        # BNNN: Jump to location NNN + V0
        pc = (opcode & 0x0FFF) + V[0x0]
    elif case1 == 0xC000:
        # CXNN: Set VX to a random number AND NN
        V[(opcode & 0x0F00) >> 8] = randrange(0x0, 0xFF) & (opcode & 0x00FF)
    elif case1 == 0xD000:
        # DXYN: Draw N-byte sprite from memory location I at (VX,VY), set VF on collision
        x = V[(opcode & 0x0F00) >> 8]
        y = V[(opcode & 0x00F0) >> 4]
        bytes = opcode & 0x000F

        V[0xF] = 0

        for row in range(bytes):
            for col in range(8):
                pixel = memory[I+row]
                
                if pixel & (0x80 >> col) != 0:
                    # By applying a modulo operation positions outiside the screen will be
                    # wrapped to the other side
                    pos_x = (x+col) % 64
                    pos_y = (y+row) % 32

                    if screen[pos_x, pos_y] == 0xFFFFFF:
                        screen[pos_x, pos_y] = 0x0
                        V[0xF] = 1
                    else:
                        screen[pos_x, pos_y] = 0xFFFFFF
    elif case1 == 0xE000:
        case2 = opcode & 0x00FF
        if case2 == 0x009E:
            # EX9E: Skip next instruction if key VX is pressed
            if keys[V[(opcode & 0x0F00) >> 8]] == 1:
                pc += 2
        elif case2 == 0x00A1:
            # EXA1: Skip next instruction if key VX is not pressed
            if keys[V[(opcode & 0x0F00) >> 8]] == 0:
                pc += 2
    elif case1 == 0xF000:
        case2 = opcode & 0x00FF
        if case2 == 0x0007:
            # FX07: Set VX to the delay timer value
            V[(opcode & 0x0F00) >> 8] = delay_timer
        elif case2 == 0x000A:
            # FX0A: Wait until a key is pressed, then store it in VX
            pressed = False
            for key in range(16):
                if keys[key] == 1:
                    V[(opcode & 0x0F00) >> 8] = key
                    pressed = True

            if not pressed:
                # Decrement pc to repeat the current opcode
                pc -= 2
        elif case2 == 0x0015:
            # FX15: Set the delay timer to VX
            delay_timer = V[(opcode & 0x0F00) >> 8]
        elif case2 == 0x0018:
            # FX18: Set the sound timer to VX
            sound_timer = V[(opcode & 0x0F00) >> 8]
        elif case2 == 0x001E:
            # FX1E: Set I to I + VX
            I = I + V[(opcode & 0x0F00) >> 8]
        elif case2 == 0x0029:
            # FX29: Set I to the memory location of font character VX
            I = V[(opcode & 0x0F00) >> 8] * 5
        elif case2 == 0x0033:
            # FX33: Store the binary coded decimal representation of VX in memory
            # starting at location I
            memory[I] = V[(opcode & 0x0F00) >> 8] / 100
            memory[I+1] = (V[(opcode & 0x0F00) >> 8] / 10) % 10
            memory[I+2] = (V[(opcode & 0x0F00) >> 8] % 100) % 10
        elif case2 == 0x0055:
            # FX55: Store registers V0 to VX in memory starting at I
            for i in range(((opcode & 0x0F00) >> 8) + 1):
                memory[I + i] = V[i]
        elif case2 == 0x0065:
            # FX65: Read registers V0 to VX from memory starting at I
            for i in range(((opcode & 0x0F00) >> 8) + 1):
                V[i] = memory[I + i]

if __name__ == "__main__":
    pygame.init()

    pc = 0x200
    opcode = 0
    I = 0
    sp = 0

    delay_timer = 0
    sound_timer = 0

    stack = np.zeros(16, dtype=np.uint16)
    V = np.zeros(16, dtype=np.uint8)
    keys = np.zeros(16)
    memory = np.zeros(4096, dtype=np.uint8)

    window = pygame.display.set_mode((512, 256))

    screen_surface = pygame.Surface((64, 32))
    screen = pygame.PixelArray(screen_surface)

    # The font characters are 5 bytes each: 0123456789ABCDEF
    memory[0x0: 0x50] = [
        0xF0, 0x90, 0x90, 0x90, 0xF0,
        0x20, 0x60, 0x20, 0x20, 0x70,
        0xF0, 0x10, 0xF0, 0x80, 0xF0,
        0xF0, 0x10, 0xF0, 0x10, 0xF0,
        0x90, 0x90, 0xF0, 0x10, 0x10,
        0xF0, 0x80, 0xF0, 0x10, 0xF0,
        0xF0, 0x80, 0xF0, 0x90, 0xF0,
        0xF0, 0x10, 0x20, 0x40, 0x40,
        0xF0, 0x90, 0xF0, 0x90, 0xF0,
        0xF0, 0x90, 0xF0, 0x10, 0xF0,
        0xF0, 0x90, 0xF0, 0x90, 0x90,
        0xE0, 0x90, 0xE0, 0x90, 0xE0,
        0xF0, 0x80, 0x80, 0x80, 0xF0,
        0xE0, 0x90, 0x90, 0x90, 0xE0,
        0xF0, 0x80, 0xF0, 0x80, 0xF0, 
        0xF0, 0x80, 0xF0, 0x80, 0x80
    ]

    filename = "Chip-8 Demos/Trip8 Demo (2008) [Revival Studios].ch8"

    with open(filename, "rb") as f:
        byte = f.read(1)
        pos = 0
        while byte != "":
            memory[0x200 + pos] = ord(byte)

            byte = f.read(1)
            pos += 1

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        state = pygame.key.get_pressed()
        # The input keys are mapped to the original keypad layout:
        # 123C
        # 456D
        # 789E
        # A0BF
        keys[0:16] = [
            state[pygame.K_x], state[pygame.K_1], state[pygame.K_2], state[pygame.K_3],
            state[pygame.K_q], state[pygame.K_w], state[pygame.K_e], state[pygame.K_a],
            state[pygame.K_s], state[pygame.K_d], state[pygame.K_z], state[pygame.K_c],
            state[pygame.K_4], state[pygame.K_r], state[pygame.K_f], state[pygame.K_v]
        ]

        for i in range(14):
            opcode = memory[pc] << 8 | memory[pc+1]
            #print("PC={:04X}, OP={:04X}, V={}, DT={}".format(pc, opcode, V, delay_timer))
            execute_opcode(opcode)
            pc += 2

        if delay_timer > 0: delay_timer -= 1

        if sound_timer > 0:
            sound_timer -= 1

            if sound_timer == 0:
                #BEEP
                pass

        scaled_surface = pygame.transform.scale(screen_surface, (512, 256))
        window.blit(scaled_surface, (0, 0))

        pygame.display.flip()