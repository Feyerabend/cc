var n, fact, i;
procedure factorial;
    begin
        fact := 1;
        i := 1;
        while i <= n do
            begin
                fact := fact * i;
                i := i + 1
            end
    end;
begin
    ?n;
    call factorial;
    !fact
end.