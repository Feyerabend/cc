
class Interpreter {

    constructor(canvas) {
        this.stack = [];
        this.systemdict = {};
        this.ctx = canvas.getContext('2d');

        this.definePrimitives();
    }

    definePrimitives() {
        this.systemdict['def'] = () => this.def();
        this.systemdict['if'] = () => this.ifOp();
        this.systemdict['ifelse'] = () => this.ifelse();
        this.systemdict['for'] = () => this.forOp();
        this.systemdict['repeat'] = () => this.repeat();
        this.systemdict['load'] = () => this.load();
        this.systemdict['add'] = () => this.add();
        this.systemdict['sub'] = () => this.sub();
        this.systemdict['mul'] = () => this.mul();
        this.systemdict['div'] = () => this.div();
        this.systemdict['eq'] = () => this.eq();
        this.systemdict['dup'] = () => this.dup();
        this.systemdict['exch'] = () => this.exch();
        this.systemdict['moveto'] = () => this.moveto();
        this.systemdict['lineto'] = () => this.lineto();
        this.systemdict['stroke'] = () => this.stroke();
        this.systemdict['setrgbcolor'] = () => this.setrgbcolor();
        this.systemdict['showpage'] = () => this.showpage();
    }

    // stack manipulation: def, dup, exch
    def() {
        const value = this.stack.pop();
        const key = this.stack.pop();
        this.systemdict[key] = value;
    }

    dup() {
        const value = this.stack[this.stack.length - 1];
        this.stack.push(value);
    }

    exch() {
        const a = this.stack.pop();
        const b = this.stack.pop();
        this.stack.push(a);
        this.stack.push(b);
    }

    // arithmetic
    add() {
        const a = this.stack.pop();
        const b = this.stack.pop();
        this.stack.push(a + b);
    }

    sub() {
        const a = this.stack.pop();
        const b = this.stack.pop();
        this.stack.push(b - a);
    }

    mul() {
        const a = this.stack.pop();
        const b = this.stack.pop();
        this.stack.push(a * b);
    }

    div() {
        const a = this.stack.pop();
        const b = this.stack.pop();
        this.stack.push(b / a);
    }

    eq() {
        const a = this.stack.pop();
        const b = this.stack.pop();
        this.stack.push(a === b);
    }

    // control flow
    ifOp() {
        const condition = this.stack.pop();
        const proc = this.stack.pop();
        if (condition) {
            this.execute(proc);
        }
    }

    ifelse() {
        const falseProc = this.stack.pop();
        const trueProc = this.stack.pop();
        const condition = this.stack.pop();
        if (condition) {
            this.execute(trueProc);
        } else {
            this.execute(falseProc);
        }
    }

    repeat() {
        const proc = this.stack.pop();
        const count = this.stack.pop();
        for (let i = 0; i < count; i++) {
            this.execute(proc);
        }
    }

    forOp() {
        const proc = this.stack.pop();
        const end = this.stack.pop();
        const incr = this.stack.pop();
        const start = this.stack.pop();
        for (let i = start; i <= end; i += incr) {
            this.stack.push(i);
            this.execute(proc);
        }
    }

    // loading values
    load() {
        const key = this.stack.pop();
        this.stack.push(this.systemdict[key]);
    }

    // drawing: moveto, lineto, setrgbcolor, stroke, showpage
    moveto() {
        const y = this.stack.pop();
        const x = this.stack.pop();
        this.ctx.moveTo(x, y);
    }

    lineto() {
        const y = this.stack.pop();
        const x = this.stack.pop();
        this.ctx.lineTo(x, y);
    }

    setrgbcolor() {
        const b = this.stack.pop();
        const g = this.stack.pop();
        const r = this.stack.pop();
        this.ctx.strokeStyle = `rgb(${r * 255}, ${g * 255}, ${b * 255})`;
    }

    stroke() {
        this.ctx.stroke();
    }

    showpage() {
        this.ctx.beginPath(); // clear current path
    }

    // a procedure (array of operations)
    execute(proc) {
        proc.forEach(op => {
            if (typeof op === 'function') {
                op();
            } else if (typeof op === 'number') {
                this.stack.push(op);
            } else if (typeof op === 'string') {
                this.systemdict[op]();
            }
        });
    }
}


const canvas = document.getElementById('canvas');
const ps = new Interpreter(canvas);

// example: move to (100, 100), draw a line to (200, 200), and stroke the line
ps.stack.push(100, 100);
ps.systemdict['moveto']();
ps.stack.push(200, 200);
ps.systemdict['lineto']();
ps.systemdict['stroke']();
