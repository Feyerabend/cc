var x, fact, i;
begin
    ? x;
    fact := 1;
    i := 1;
    while i <= x do
    begin
        fact := fact * i;
        i := i + 1
    end;
    if fact > 100 then
        ! fact
end.