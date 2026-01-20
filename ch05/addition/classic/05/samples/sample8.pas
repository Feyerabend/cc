var a, b, gcd;

procedure computeGCD;
begin
    while (b # 0) do
    begin
        if (a > b) then
            a := a - b;
        if (a <= b) then
            b := b - a;
    end;
    gcd := a;
end;

begin
    a := 48;
    b := 18;
    call computeGCD;
end.