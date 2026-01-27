var n, sum, i;
begin
    ? n;
    sum := 0;
    i := 1;
    while i <= n do
    begin
        sum := sum + i;
        i := i + 1
    end;
    ! sum;
end.