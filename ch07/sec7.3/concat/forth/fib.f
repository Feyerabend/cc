: FIB
  DUP 1 <= IF
    DROP 1
  ELSE
    1 1 ROT 2 - 0 DO
      OVER + SWAP
    LOOP
    DROP
  THEN
;

7 FIB .
BYE
