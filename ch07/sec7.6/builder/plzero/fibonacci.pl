var n, a, b, temp, count;

begin
  ? n;
  a := 0;
  b := 1;
  count := 0;
  
  while count < n do
  begin
    ! a;
    temp := a + b;
    a := b;
    b := temp;
    count := count + 1;
  end;
end.
