var x, y, z;
procedure multiply;
begin
  z := 0;
  while x > 0 do
  begin
    z := z + y;
    x := x - 1
  end
end;
begin
  ? x;
  ? y;
  call multiply;
  ! z
end.
