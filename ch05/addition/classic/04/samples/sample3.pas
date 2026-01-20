const max = 10;
var a, b, fib, counter;

begin
    a := 0;
    b := 1;
    counter := 1;
    fib := a;

    while (counter <= max) do
    begin
        fib := a + b;
        a := b;
        b := fib;
        counter := counter + 1;
    end;
end.