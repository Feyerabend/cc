var global;

procedure math;
var a, b;
begin
  ? a;
  ? b;
  if a < b then ! a;
  if b < a then ! b;
  global := a + b;
end;

begin
  call math;
  ! global * 2;
end.