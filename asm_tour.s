// asm_tour.s - a literate tour of ARM64 assembly on macOS.
//
// Read this file from top to bottom. Each section shows what one familiar
// idea looks like when there is no compiler: printing text, a function call,
// an `if`, a loop, printing a number. Each section prints one line when it
// runs, so the program's output is its own table of contents.
//
// Build, run, and look inside:
//
//   clang -o asm_tour asm_tour.s     assemble and link
//   ./asm_tour                       run it
//   objdump -d -M no-aliases asm_tour
//                                    the instructions the CPU actually gets
//
// That last one has a surprise in it. Several instructions in this file do
// not exist. They are aliases, nicer names the assembler rewrites into real
// instructions: `mov x2, x4` is really `orr x2, xzr, x4`, and `cmp x0, #0`
// is really `subs xzr, x0, #0`. Drop `-M no-aliases` to see the nice names.
//
// The best way to read it is to step through it in the debugger, one
// instruction at a time, and watch the registers change:
//
//   lldb ./asm_tour
//   (lldb) b main                    stop at the first instruction of main
//   (lldb) run
//   (lldb) si                        step one instruction, into calls
//   (lldb) ni                        step one instruction, over calls
//   (lldb) register read x0 x1 x30 sp
//   (lldb) disassemble               the instructions around where you are
//
//
// HOW TO READ A LINE
//
//   add     x0, x1, x2       // x0 = x1 + x2
//
// The instruction comes first, then its operands. The destination is always
// the first operand. Everything after `//` is a comment.
//
// The CPU has 31 general-purpose registers, x0 to x30, each 64 bits wide.
// They are the only variables an instruction can do arithmetic on. Writing
// w0 instead of x0 means "the low 32 bits of x0". A few have special jobs:
//
//   sp     the stack pointer (section 3)
//   x29    the frame pointer (section 3)
//   x30    the link register: where `ret` goes back to (section 3)
//   xzr    reads as zero; writes to it are thrown away
//
//
// TALKING TO THE KERNEL
//
// A program can compute on its own, but it cannot print or exit without the
// kernel. It asks with a system call: put the syscall's number in x16, its
// arguments in x0, x1, x2 and so on, then run `svc #0x80`, which traps into
// the kernel. The kernel does the work and comes back to the next instruction.
//
// This program never calls libc. Every bit of output is a raw `write`
// syscall. That is not how real macOS programs work: macOS does not promise
// that syscall numbers stay the same between releases, and everything is
// meant to go through libSystem instead. Here, seeing the kernel boundary is
// the point. If a number changes one day, the two .equ lines below are the
// only place to fix.
//
// On Linux the idea is the same and the details differ: the number goes in
// x8 instead of x16, the trap is `svc #0`, the numbers are different (write
// is 64, exit is 93), and symbols have no leading underscore (`main`, not
// `_main`). The `@PAGE` address syntax in section 2 is also macOS-only.

        .equ    SYS_exit, 1
        .equ    SYS_write, 4
        .equ    STDOUT, 1               // file descriptor 1 is standard output

// Code lives in the text section, and data lives in the data section. The
// sections below switch between the two, so each string sits next to the code
// that prints it. The linker gathers each kind into one place at the end.
//
// Every ARM64 instruction is exactly 4 bytes, and must start at an address
// that is a multiple of 4. `.p2align 2` means "align to 2^2 bytes".

        .text
        .p2align 2
        .global _main                   // let the linker see main


// =============================================================================
// main
// =============================================================================
//
// main is the table of contents. Each `bl` runs one section; section 3
// explains how `bl` works. The C runtime calls _main when the program starts,
// just as it would for a C program.

_main:
        bl      section_hello           // section 2
        bl      section_functions       // section 3
        bl      section_conditionals    // section 4
        bl      section_loops           // section 5
        bl      section_numbers         // section 6

// -----------------------------------------------------------------------------
// Section 1: exit
// -----------------------------------------------------------------------------
//
// The smallest complete program is these three instructions. It runs last
// and prints nothing; check that it worked with `echo $?` after running.
//
// `exit` takes one argument, the exit status, so it goes in x0. Zero means
// success. The program ends inside the kernel, and nothing after `svc` runs.
//
// main never returns, because it exits instead. Section 3 shows why that
// matters: it is the reason main gets away without saving x30.

        mov     x0, #0                  // exit status 0
        mov     x16, #SYS_exit          // which syscall
        svc     #0x80                   // trap into the kernel; never returns


// -----------------------------------------------------------------------------
// Section 2: hello
// -----------------------------------------------------------------------------
//
// `write(fd, buffer, length)` takes three arguments, so they go in x0, x1, x2.
// The buffer is an address. A string in memory has no length attached to it,
// so the length has to be passed separately.

        .data
hello_msg:
        .ascii  "2. Hello: one write syscall, no libc.\n"
        .equ    hello_len, . - hello_msg
        .text

// `.ascii` places those bytes in memory, and `hello_msg` is the address of
// the first one. `.` means "the address the assembler has reached", so
// `. - hello_msg` is the string's length. The assembler counts it for us.
//
// Getting an address into a register takes two instructions. An instruction
// is only 4 bytes, so it has no room for a full 64-bit address. `adrp` gets
// the address of the 4 KB page the string is on, relative to this code, and
// `add` adds the string's offset within that page.

section_hello:
        mov     x0, #STDOUT                     // fd
        adrp    x1, hello_msg@PAGE              // buffer: the page...
        add     x1, x1, hello_msg@PAGEOFF       // ...plus the offset in it
        mov     x2, #hello_len                  // length
        mov     x16, #SYS_write
        svc     #0x80
        ret                                     // back to main; see section 3


// -----------------------------------------------------------------------------
// Section 3: functions
// -----------------------------------------------------------------------------
//
// A function is just a label to jump to. The hard part is getting back.
//
//   bl  print     "branch with link": put the address of the next
//                 instruction in x30, then jump to `print`
//   ret           jump to the address in x30
//
// So x30 is where to go home to. There is only one x30. Section 2 was safe,
// because it called nothing, so x30 still held main's address when it
// reached `ret`. Now consider a function that calls another function:
//
//   outer:
//           bl      print      // x30 = the address of the next line...
//           ret                // ...so this jumps to itself, forever
//
// The inner `bl` overwrote outer's way home. The fix is to save x30 in
// memory before calling anything, and restore it before `ret`. The memory
// for that is the stack.
//
//
// THE STACK
//
// sp holds an address. Below it is free memory; at and above it are the
// saved values of every function that is still running. To save something,
// move sp down and store at the new sp. To restore, load and move sp back.
// On ARM64, sp must always be a multiple of 16.
//
//   stp  x29, x30, [sp, #-16]!    store the pair x29, x30 at sp - 16, and
//                                 (the `!`) set sp to sp - 16 first
//   ldp  x29, x30, [sp], #16      load the pair from sp, then add 16 to sp
//
// x29 is the frame pointer. Pointing it at the saved pair links each frame
// to the one before, which is how the debugger's `bt` command finds the
// chain of callers. macOS requires every function that has a frame to do
// this.
//
//
// THE CALLING CONVENTION
//
// Nothing in the CPU says arguments go in x0. It is an agreement, so that
// code written by different people can call each other. The main rules:
//
//   x0-x7      arguments. The result comes back in x0.
//   x9-x15     scratch. A function you call may change these.
//   x19-x28    a function you call must leave these as it found them.
//              If it wants to use one, it saves it first (section 5).
//   x16, x17   scratch, used between calls. This file uses x16 for
//              syscall numbers.
//   x18        reserved by macOS. Do not touch it.
//
// `print` below takes the place of the syscall in section 2. It is a leaf
// (it calls nothing), so it needs no frame.

        .data
functions_msg:
        .ascii  "3. Functions: this line came through print(pointer, length).\n"
        .equ    functions_len, . - functions_msg
        .text

// print(x0 = pointer, x1 = length)
print:
        mov     x2, x1                  // write wants the length in x2,
        mov     x1, x0                  // the pointer in x1,
        mov     x0, #STDOUT             // and the fd in x0
        mov     x16, #SYS_write
        svc     #0x80
        ret

// The usual shape of a function that calls others: save the frame, do the
// work, restore the frame, return. The first two and last two lines are
// called the prologue and the epilogue.

section_functions:
        stp     x29, x30, [sp, #-16]!   // prologue: save the way home
        mov     x29, sp

        adrp    x0, functions_msg@PAGE
        add     x0, x0, functions_msg@PAGEOFF
        mov     x1, #functions_len
        bl      print                   // this overwrites x30...

        ldp     x29, x30, [sp], #16     // ...and this puts it back
        ret


// -----------------------------------------------------------------------------
// Section 4: conditionals
// -----------------------------------------------------------------------------
//
// There is no `if` instruction. An `if` takes two steps:
//
//   cmp   x0, #0       subtract 0 from x0, throw the answer away, and keep
//                      four flag bits about it: negative, zero, carry,
//                      overflow. (It throws the answer away by writing it
//                      to xzr. See the alias note at the top.)
//   b.ge  somewhere    branch if the flags say "greater or equal";
//                      otherwise carry on to the next instruction
//
// The other conditions include eq, ne, lt, le and gt. They all read the
// flags from the most recent instruction that set them.
//
// Note that `if (n < 0) { A } else { B }` tests the opposite condition. The
// branch jumps over A when n is NOT negative:
//
//           cmp     n, #0
//           b.ge    else       // not negative: skip A
//           A
//           b       end        // done with A: skip B
//   else:   B
//   end:
//
// Labels that start with L are local. They do not appear in the symbol
// table, so the debugger does not mistake them for functions.
//
// We cannot print numbers until section 6, so the -7 and 42 inside these
// strings are typed by hand.

        .data
branch_msg:
        .ascii  "4. Conditionals, with a branch: -7 is "
        .equ    branch_len, . - branch_msg
csel_msg:
        .ascii  "4. Conditionals, with csel:     42 is "
        .equ    csel_len, . - csel_msg
negative_word:
        .ascii  "negative.\n"
        .equ    negative_len, . - negative_word
not_negative_word:
        .ascii  "not negative.\n"
        .equ    not_negative_len, . - not_negative_word
        .text

section_conditionals:
        stp     x29, x30, [sp, #-32]!   // 32 bytes this time: room for x19
        mov     x29, sp
        str     x19, [sp, #16]          // we use x19, so save the caller's

        adrp    x0, branch_msg@PAGE
        add     x0, x0, branch_msg@PAGEOFF
        mov     x1, #branch_len
        bl      print

        // if (n < 0) print "negative" else print "not negative"
        //
        // n lives in x19, not a scratch register like x9, because the `bl`
        // above would have been free to change x9.
        mov     x19, #-7
        cmp     x19, #0
        b.ge    Lcond_not_negative
        adrp    x0, negative_word@PAGE
        add     x0, x0, negative_word@PAGEOFF
        mov     x1, #negative_len
        bl      print
        b       Lcond_done
Lcond_not_negative:
        adrp    x0, not_negative_word@PAGE
        add     x0, x0, not_negative_word@PAGEOFF
        mov     x1, #not_negative_len
        bl      print
Lcond_done:

        // The same choice, with no branch at all.
        //
        //   csel  x0, x1, x2, lt      x0 = lt ? x1 : x2
        //
        // Load both answers, compare, and let csel pick one. A branch can
        // make the CPU guess which way the program goes, and a wrong guess
        // costs time. csel has nothing to guess. Compilers turn small `?:`
        // expressions into this.
        adrp    x0, csel_msg@PAGE
        add     x0, x0, csel_msg@PAGEOFF
        mov     x1, #csel_len
        bl      print

        mov     x19, #42
        adrp    x0, negative_word@PAGE          // answer if negative
        add     x0, x0, negative_word@PAGEOFF
        mov     x1, #negative_len
        adrp    x2, not_negative_word@PAGE      // answer if not
        add     x2, x2, not_negative_word@PAGEOFF
        mov     x3, #not_negative_len
        cmp     x19, #0
        csel    x0, x0, x2, lt                  // pick the pointer...
        csel    x1, x1, x3, lt                  // ...and its length
        bl      print

        ldr     x19, [sp, #16]          // restore the caller's x19
        ldp     x29, x30, [sp], #32
        ret


// -----------------------------------------------------------------------------
// Section 5: loops
// -----------------------------------------------------------------------------
//
// A loop is a branch that goes backwards. `while (cond) { body }` is:
//
//   top:    if not cond, branch to done
//           body
//           b       top
//   done:
//
// The first loop finds the length of a string, so we can stop counting
// lengths by hand. C marks the end of a string with a zero byte, and
// `.asciz` adds one for us. strlen walks a pointer forward until it loads
// that zero.
//
//   ldrb  w2, [x1]     load the one byte at address x1 into w2
//   cbz   w2, done     "compare and branch if zero": a cmp and a b.eq
//                      in one instruction

// strlen(x0 = pointer) -> x0 = length
strlen:
        mov     x1, x0                  // x1 walks; x0 remembers the start
Lstrlen_loop:
        ldrb    w2, [x1]
        cbz     w2, Lstrlen_done        // found the zero byte: stop
        add     x1, x1, #1              // next byte
        b       Lstrlen_loop
Lstrlen_done:
        sub     x0, x1, x0              // length = end - start
        ret

// print_cstr(x0 = pointer to a zero-terminated string)
//
// This needs x0 after calling strlen, but strlen is free to change x0. So
// keep it in x19, which survives calls, and save the caller's x19 first.
// From here on every string is printed with this.
print_cstr:
        stp     x29, x30, [sp, #-32]!
        mov     x29, sp
        str     x19, [sp, #16]

        mov     x19, x0                 // keep the pointer safe
        bl      strlen                  // x0 = length
        mov     x1, x0                  // print(pointer, length)
        mov     x0, x19
        bl      print

        ldr     x19, [sp, #16]
        ldp     x29, x30, [sp], #32
        ret

// The second loop is a counted one: `for (i = 10; i != 0; i--)`. Counting
// down to zero saves a cmp, because cbnz tests for zero directly. The
// counter must survive the call to print_cstr, so it lives in x19 too.

        .data
loops_msg:
        .asciz  "5. Loops: strlen measured this line.\n"
counted_msg:
        .asciz  "5. Loops, counted: "
star:
        .asciz  "*"
newline:
        .asciz  "\n"
        .text

section_loops:
        stp     x29, x30, [sp, #-32]!
        mov     x29, sp
        str     x19, [sp, #16]

        adrp    x0, loops_msg@PAGE
        add     x0, x0, loops_msg@PAGEOFF
        bl      print_cstr

        adrp    x0, counted_msg@PAGE
        add     x0, x0, counted_msg@PAGEOFF
        bl      print_cstr

        mov     x19, #10                // i = 10
Lstars_loop:
        adrp    x0, star@PAGE
        add     x0, x0, star@PAGEOFF
        bl      print_cstr
        sub     x19, x19, #1            // i--
        cbnz    x19, Lstars_loop        // "compare and branch if not zero"

        adrp    x0, newline@PAGE
        add     x0, x0, newline@PAGEOFF
        bl      print_cstr

        ldr     x19, [sp, #16]
        ldp     x29, x30, [sp], #32
        ret


// -----------------------------------------------------------------------------
// Section 6: numbers
// -----------------------------------------------------------------------------
//
// The number 42 in a register is the bits 101010. To print it we need the
// characters '4' and '2'. Getting from one to the other is what printf does
// for you.
//
// Dividing by 10 gives the last digit as the remainder: 42 / 10 is 4,
// remainder 2. Repeat on the 4 to get the next digit. The digits come out
// last one first, so write them into a buffer from the end towards the
// start, and print from wherever we stopped.
//
// There is no remainder instruction. Divide, then multiply back and subtract:
//
//   udiv  q, n, ten          q = n / 10       (rounded down)
//   msub  r, q, ten, n       r = n - q * 10   (the remainder)
//
// A digit's character is its value plus the character code of '0', because
// '0' to '9' are consecutive in ASCII.
//
// The buffer lives on the stack. The largest 64-bit number has 19 digits,
// plus one for a minus sign, so 32 bytes is plenty. The frame is 48 bytes:
// 16 for the saved x29 and x30, then 32 for the buffer.
//
//   sp + 0    saved x29, x30
//   sp + 16   buffer start
//   sp + 48   buffer end: the first digit is stored just below here

// print_number(x0 = a signed 64-bit integer)
print_number:
        stp     x29, x30, [sp, #-48]!
        mov     x29, sp

        add     x1, sp, #48             // x1 = the end of the buffer
        mov     x3, #10

        // Work on the magnitude. `cneg` is csel's cousin: negate if lt. The
        // most negative number, -9223372036854775808, has no positive
        // twin, so cneg leaves it unchanged. Read as unsigned by udiv, those
        // same bits are +9223372036854775808, so it still prints correctly.
        cmp     x0, #0
        cneg    x2, x0, lt              // x2 = |n|

        // This loop tests at the bottom: a do-while. So 0 still prints "0".
Ldigit_loop:
        udiv    x4, x2, x3              // x4 = x2 / 10
        msub    x5, x4, x3, x2          // x5 = x2 % 10, the last digit
        add     x5, x5, #'0'            // the digit's character
        sub     x1, x1, #1              // step back one byte...
        strb    w5, [x1]                // ...and store the character there
        mov     x2, x4                  // carry on with what is left
        cbnz    x2, Ldigit_loop

        // x0 was not touched, so the flags can be set from it again.
        cmp     x0, #0
        b.ge    Lno_sign
        mov     w5, #'-'
        sub     x1, x1, #1
        strb    w5, [x1]
Lno_sign:
        add     x2, sp, #48             // length = buffer end - x1
        sub     x2, x2, x1
        mov     x0, x1                  // print(x1, length)
        mov     x1, x2
        bl      print

        ldp     x29, x30, [sp], #48
        ret

// Each number is one call. `mov` can put the most negative number in a
// register in one instruction, because its bits are a single 1 followed by
// 63 zeros, and mov can place a 16-bit chunk anywhere in the register.

        .data
numbers_msg:
        .asciz  "6. Numbers:"
space:
        .asciz  " "
        .text

section_numbers:
        stp     x29, x30, [sp, #-16]!
        mov     x29, sp

        adrp    x0, numbers_msg@PAGE
        add     x0, x0, numbers_msg@PAGEOFF
        bl      print_cstr

        adrp    x0, space@PAGE
        add     x0, x0, space@PAGEOFF
        bl      print_cstr
        mov     x0, #0
        bl      print_number

        adrp    x0, space@PAGE
        add     x0, x0, space@PAGEOFF
        bl      print_cstr
        mov     x0, #-7
        bl      print_number

        adrp    x0, space@PAGE
        add     x0, x0, space@PAGEOFF
        bl      print_cstr
        mov     x0, #0x8000000000000000         // -9223372036854775808
        bl      print_number

        adrp    x0, newline@PAGE
        add     x0, x0, newline@PAGEOFF
        bl      print_cstr

        ldp     x29, x30, [sp], #16
        ret
