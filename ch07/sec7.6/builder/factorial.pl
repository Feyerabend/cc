var n, result;

procedure factorial;
var i;
begin
  result := 1;
  i := 1;
  while i < n + 1 do
  begin
    result := result * i;
    i := i + 1;
  end;
end;

begin
  ? n;
  call factorial;
  ! result;
end.
