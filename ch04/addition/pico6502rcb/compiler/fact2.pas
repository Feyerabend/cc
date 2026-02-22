VAR cursor_x, cursor_y, char_to_print, number_to_print, fact, n, i, buttons;

PROCEDURE print_char;
VAR addr;
BEGIN
    addr := cursor_y * 40 + cursor_x;
    WRITE char_to_print TO SCREEN + addr;
    WRITE 1 TO COLOR + addr;        // white text
    cursor_x := cursor_x + 1;
    IF cursor_x = 40 THEN
    BEGIN
        cursor_x := 0;
        cursor_y := cursor_y + 1
    END
END;

PROCEDURE print_number;
VAR digit, temp;
BEGIN
    IF number_to_print = 0 THEN
    BEGIN
        char_to_print := 48;        // '0'
        CALL print_char
    END
    ELSE
    BEGIN
        digit := number_to_print - (number_to_print / 10) * 10;
        temp := number_to_print / 10;
        number_to_print := temp;
        IF temp > 0 THEN CALL print_number;
        char_to_print := digit + 48;
        CALL print_char
    END
END;

BEGIN
    WRITE 0 TO BORDER;
    WRITE 0 TO BGCOLOR;

    cursor_x := 2;
    cursor_y := 12;

    // Print "FACTORIAL 8! = "
    char_to_print := 70; CALL print_char;  // F
    char_to_print := 65; CALL print_char;  // A
    char_to_print := 67; CALL print_char;  // C
    char_to_print := 84; CALL print_char;  // T
    char_to_print := 79; CALL print_char;  // O
    char_to_print := 82; CALL print_char;  // R
    char_to_print := 73; CALL print_char;  // I
    char_to_print := 65; CALL print_char;  // A
    char_to_print := 76; CALL print_char;  // L
    char_to_print := 32; CALL print_char;  // space
    char_to_print := 56; CALL print_char;  // 8
    char_to_print := 33; CALL print_char;  // !
    char_to_print := 32; CALL print_char;  // space
    char_to_print := 61; CALL print_char;  // =
    char_to_print := 32; CALL print_char;  // space

    n := 8;
    fact := 1;
    i := n;
    WHILE i > 1 DO
    BEGIN
        fact := fact * i;
        i := i - 1
    END;

    number_to_print := fact;
    CALL print_number;

    OUT fact;                           // debug output of the raw value

    // React to input forever
    WHILE 1 = 1 DO
    BEGIN
        IN buttons;
        WRITE buttons TO BORDER         // border color follows button state
    END
END.
