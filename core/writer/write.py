from typing import Iterable
import keyboard as kb
import numpy as np
import time

DEBUG = True
DO_NOT_WRITE = True

def write(data: str):
    if DEBUG:
        print(data)
    if DO_NOT_WRITE:
        return

    kb.press('t')
    time.sleep(0.05)
    kb.write(data)
    time.sleep(0.02)
    kb.press('enter')

def breakValues():
    print("Breaking. ", end='')
    input("Press any key...")
    time.sleep(1)


def move(x = 0, y = 0, z = 0):
    write("/minecraft:tp @p ~{} ~{} ~{}".format(x,y,z))
def goto(cord):
    write("/minecraft:tp @p {} {} {}".format(cord[0], cord[1], cord[2]))
def set_block(block_name, offset_x = 0, offset_y = 0, offset_z = 0):
    write("/minecraft:setblock ~{} ~{} ~{} minecraft:{}".format(offset_x, offset_y, offset_z, block_name))

def set_bit(value: bool, offset_x = 0, offset_y = 0, offset_z = 0, LOW_BIT = "redstone_block", HIGH_BIT = "lime_glazed_terracotta"):
    if value:
        set_block(HIGH_BIT, offset_x, offset_y, offset_z)
    else:
        set_block(LOW_BIT, offset_x, offset_y, offset_z)
def write_num(value: int, start_pos, stride, offset, low_bit, high_bit, shape = (None, None, 8), breaks = (False, False, False)):
    start_pos = np.array(start_pos)
    stride = np.array(stride)
    offset = np.array(offset)

    binval = bin(value)[2:]
    if shape[2] != None:
        if len(binval) < shape[2]:
            binval = '0'*(shape[2]-len(binval))+binval
    for i, bit in enumerate(reversed(binval)):
        new_cords = start_pos+stride*i
        goto(new_cords)
        set_bit(bit=='1', offset[0], offset[1], offset[2], low_bit, high_bit)
        
        if breaks[2]:
            breakValues()
        if shape[2] is not None and shape[2] < i:
            print('Skiping x')
            return

def write_sequence(iterable: Iterable, start_pos, stride_row, stride_bit, place_offset, low_bit, high_bit, shape = (None, None, 8), breaks = (False, False, False)):
        start_pos = np.array(start_pos)
        stride_row = np.array(stride_row)

        for i, val in enumerate(iterable):
            new_cords = start_pos+stride_row*i
            write_num(val, new_cords, stride_bit, place_offset, low_bit, high_bit)
            if breaks[1]:
                breakValues()
            if shape[1] is not None and shape[1] < i:
                print('Skiping y')
                return


def write_block_sequence(iterable: Iterable, start_pos, stride_row, stride_block, stride_bit, place_offset, low_bit="redstone_block", high_bit="lime_glazed_terracotta", shape = (None, None, 8), breaks = (False, False, False)):
    stride_block = np.array(stride_block)
    start_pos = np.array(start_pos)

    for i, block in enumerate(iterable):
        block_start = start_pos+stride_block*i
        write_sequence(block, block_start, stride_row, stride_bit, place_offset, low_bit, high_bit)
        if breaks[0]:
            breakValues()
        if shape[0] is not None and shape[0] < i:
            print('Skiping z')
            return


def main():
    time.sleep(0.5)

    START = (1240, 43, 301)
    START = (1183, 79, 472)

    write_block_sequence([[255,1,2,3], [5,6,7,8], [5,6,7,8]], START, (3, 0, 0), (0,-1,0), (0, 8, 0), (0, 0, -2))


if __name__ == "__main__":
    main()