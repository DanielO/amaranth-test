setMode -bscan
setCable -target "xilinx_tcf URL=tcp:127.0.0.1:3121"
identify
assignFile -p 2 -file build/top.bit
program -p 2
exit

