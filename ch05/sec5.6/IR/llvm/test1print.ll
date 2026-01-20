@.fmt = private unnamed_addr constant [12 x i8] c"Result: %d\0A\00", align 1

declare i32 @printf(i8*, ...)

define i32 @main() {
entry:
  %t1 = add i32 10, 5

  %fmt_ptr = getelementptr inbounds [12 x i8], [12 x i8]* @.fmt, i64 0, i64 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %t1)

  ret i32 0
}

