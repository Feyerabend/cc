
```mermaid
stateDiagram-v2
    [*] --> State0
    
    State0 --> State5: num
    State0 --> State4: (
    State0 --> State1: E (goto)
    State0 --> State2: T (goto)
    State0 --> State3: F (goto)
    
    State1 --> State6: +
    State1 --> [*]: $ (accept)
    
    State2 --> State7: *
    State2 --> State2: +/)/$ (reduce by E→T)
    
    State3 --> State3: +/*/)/$ (reduce by T→F)
    
    State4 --> State5: num
    State4 --> State4: (
    State4 --> State8: E (goto)
    State4 --> State2: T (goto)
    State4 --> State3: F (goto)
    
    State5 --> State5: +/*/)/$ (reduce by F→num)
    
    State6 --> State5: num
    State6 --> State4: (
    State6 --> State9: T (goto)
    State6 --> State3: F (goto)
    
    State7 --> State5: num
    State7 --> State4: (
    State7 --> State10: F (goto)
    
    State8 --> State6: +
    State8 --> State11: )
    
    State9 --> State7: *
    State9 --> State9: +/)/$ (reduce by E→E+T)
    
    State10 --> State10: +/*/)/$ (reduce by T→T*F)
    
    State11 --> State11: +/*/)/$ (reduce by F→(E))
    
    note right of State1
        Accept state
    end note
    
    note right of State2
        Reduce: E → T
    end note
    
    note right of State3
        Reduce: T → F
    end note
    
    note right of State5
        Reduce: F → num
    end note
    
    note right of State9
        Reduce: E → E+T
    end note
    
    note right of State10
        Reduce: T → T*F
    end note
    
    note right of State11
        Reduce: F → (E)
    end note
```