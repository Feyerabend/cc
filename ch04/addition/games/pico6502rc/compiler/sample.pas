    CONST BTN_A = 1, BTN_B = 2;
    VAR buttons, x, y, color;
    
    BEGIN
        x := 0;
        y := 0;
        color := 1;
        
        WHILE 1 = 1 DO
        BEGIN
            IN buttons;
            
            IF buttons # 255 THEN
            BEGIN
                READ x FROM $D002;
                READ y FROM $D003;
                
                WRITE 42 TO SCREEN + x + y * 40;
                WRITE color TO COLOR + x + y * 40;
                
                x := x + 1;
                IF x > 39 THEN
                    x := 0;
                    
                color := color + 1;
                IF color > 15 THEN
                    color := 1
            END
        END
    END.
