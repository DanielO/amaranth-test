#!/usr/bin/env python3

# https://github.com/GlasgowEmbedded/glasgow/blob/6e6b9c1cdd28e8cdef3e9b99b67cc0fd8c3d98b4/software/glasgow/target/hardware.py

from amaranth import *
from amaranth.build import *
from amaranth.vendor.xilinx import XilinxPlatform
from .i2c import I2CTarget
from .registers import I2CRegisters

__all__ = ['I2CTest']

class I2CTest(Elaboratable):
    def elaborate(self, platform):
        m = Module()

        # I2C target & register bank
        m.submodules.i2c_target = I2CTarget(platform.request('i2c'))
        m.submodules.registers = I2CRegisters(m.submodules.i2c_target)

        # Set I2C address
        m.d.comb += m.submodules.i2c_target.address.eq(0b0001000)

        # Create registers
        self.reg_led,  self.addr_led  = m.submodules.registers.add_rw(8)
        self.reg_push,  self.addr_push  = m.submodules.registers.add_ro(8)
        self.reg_test,  self.addr_test  = m.submodules.registers.add_ro(8)
        print('led at %d, push at %d, test at %d' % (self.addr_led, self.addr_push, self.addr_test))

        # Connect LED1 to reg_led
        led1 = platform.request("led1")
        m.d.comb += led1.eq(~self.reg_led[0])

        # Read push button state in reg_push
        push1 = platform.request("push1")
        push2 = platform.request("push2")
        m.d.comb += self.reg_push.eq(push2 << 1 | push1)

        # Control led2 from push2 state
        led2 = platform.request("led2")
        m.d.comb += led2.eq(push2)

        # Dummy register with fixed value
        m.d.comb += self.reg_test.eq(123)

        # Blink LED3 at 1Hz
        led3 = platform.request("led3")
        half_freq = int(platform.default_clk_frequency // 2)
        timer = Signal(range(half_freq + 1))

        with m.If(timer == half_freq):
            m.d.sync += led3.eq(~led3)
            m.d.sync += timer.eq(0)
        with m.Else():
            m.d.sync += timer.eq(timer + 1)
        return m

def I2CResource(*args, scl, sda, conn=None, attrs=None):
    io = []
    io.append(Subsignal("scl", Pins(scl, dir="io", conn=conn, assert_width=1)))
    io.append(Subsignal("sda", Pins(sda, dir="io", conn=conn, assert_width=1)))
    if attrs is not None:
        io.append(attrs)
    return Resource.family(*args, default_name="i2c", ios=io)

class Spartan3Board(XilinxPlatform):
    '''Memec Spartan 3 evaluation board (3SxLC Rev2)'''

    device = 'xc3s400'
    package = 'pq208'
    speed = '4'
    resources = [
        Resource("clk50", 0, Pins("P184", dir="i"),
                 Attrs(IOSTANDARD="LVCMOS33"), Clock(50e6)),

        Resource("push1", 0, Pins("P22", dir="i"),
                 Attrs(IOSTANDARD="LVCMOS33", PULLUP=True)),
        Resource("push2", 0, Pins("P24", dir="i"),
                 Attrs(IOSTANDARD="LVCMOS33", PULLUP=True)),
        Resource("led1", 0, Pins("P20", dir="o"),
                 Attrs(IOSTANDARD="LVCMOS33")),
        Resource("led2", 0, Pins("P21", dir="o"),
                 Attrs(IOSTANDARD="LVCMOS33")),
        Resource("led3", 0, Pins("P18", dir="o"),
                 Attrs(IOSTANDARD="LVCMOS33")),
        Resource("led4", 0, Pins("P19", dir="o"),
                 Attrs(IOSTANDARD="LVCMOS33")),
        I2CResource(0, scl="P40", sda="P48",
                     attrs=Attrs(IOSTANDARD="LVCMOS33")),
    ]

    default_clk = 'clk50'
    connectors = []

if __name__ == '__main__':
    platform = Spartan3Board()
    top = I2CTest()
    platform.build(top)
