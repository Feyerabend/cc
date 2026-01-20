const max = 5;
var factorial, counter;

begin
    factorial := 1;
    counter := 1;

    while (counter <= max) do
    begin
        factorial := factorial * counter;
        counter := counter + 1;
    end;
end.
