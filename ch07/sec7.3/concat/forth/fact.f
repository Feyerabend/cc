: FACT ( n -- n! )
  DUP 0= IF
    DROP 1
  ELSE
    1 SWAP 1 + 1 DO I * LOOP
  THEN
;

5 FACT .
BYE
