// call by value (primitives)
function modifyValue(x) {
    x = 999;
}

function demoByValue() {
    let num = 42;
    modifyValue(num);
    console.log("By Value: " + num + " (unchanged)");
}

// call by sharing (objects)
function modifyObject(obj) {
    obj.value = 999;  // Changes the original
}

function reassignObject(obj) {
    obj = { value: 999 };  // Does NOT change the original
}

function demoBySharing() {
    let obj1 = { value: 42 };
    modifyObject(obj1);
    console.log("By Sharing (modify): " + obj1.value + " (changed)");
    
    let obj2 = { value: 42 };
    reassignObject(obj2);
    console.log("By Sharing (reassign): " + obj2.value + " (unchanged)");
}


demoByValue();
demoBySharing();

// Note: JavaScript has no true "call by reference"
// But you can simulate it with objects:
function modifyViaWrapper(wrapper) {
    wrapper.value = 999;
}

function demoSimulatedReference() {
    let wrapper = { value: 42 };
    modifyViaWrapper(wrapper);
    console.log("Simulated Reference: " + wrapper.value + " (changed)");
}

demoSimulatedReference();
