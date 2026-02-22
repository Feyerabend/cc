
    CONST BLUE = 6, CYAN = 3;
    VAR buttons, i;
    
    BEGIN
        WRITE BLUE TO BORDER;
        WRITE CYAN TO BGCOLOR;
        
        i := 0;
        WHILE i < 10 DO
        BEGIN
            WRITE 65 TO SCREEN + i;
            WRITE 1 TO COLOR + i;
            i := i + 1
        END;
        
        IN buttons;
        IF buttons # 255 THEN
            WRITE 2 TO BORDER
    END.

    

