    VAR n, result;
    
    PROCEDURE factorial;
    VAR i;
    BEGIN
        result := 1;
        i := n;
        WHILE i > 1 DO
        BEGIN
            result := result * i;
            i := i - 1
        END
    END;
    
    BEGIN
        n := 5;
        CALL factorial;
        OUT result
    END.
