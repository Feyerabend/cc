
## Multi-threaded Raytracer with Web Workers

This builds on the raytracing demo by adding *parallel processing* using Web Workers.
*Read the Raytracing [README](./../11) first*--this document only covers the parallelization aspects.


### Single-threaded Bottleneck

The original raytracer ran on a *single CPU core*:

```
Frame render time: ~100ms
Maximum FPS: 10
CPU usage: 25% (1 core of 4-core CPU)
```

*Why so slow?*
- 400×400 = 160,000 pixels per frame
- Each pixel requires multiple ray calculations
- Millions of operations per frame
- *JavaScript is single-threaded by default*


### The Solution: Web Workers

Web Workers allow JavaScript to use *multiple CPU cores* simultaneously:

```
4 workers × 4 cores = parallel processing
Frame render time: ~25ms
Maximum FPS: 40
CPU usage: 100% (all cores working)
```



### What are Web Workers? Concept

*Web Workers* are separate JavaScript execution contexts that run in the background:

```
Main Thread              Worker Thread 1
    |                          |
    |--- Send work ----------->|
    |                          | (processing)
    |                          |
    |<-- Receive result -------|
```

*Key properties:*
- Run in *separate thread* (true parallelism)
- Have *own memory space* (isolated)
- Communicate via *messages* (no shared variables)
- Cannot access *DOM* (no document, canvas, etc.)

### Browser Support

```javascript
const NUM_WORKERS = navigator.hardwareConcurrency || 4;
```

*`navigator.hardwareConcurrency`* returns number of logical CPU cores:
- Quad-core laptop: 4
- Dual-core with hyperthreading: 4
- Eight-core desktop: 8
- Mobile phone: 4-8

*Fallback to 4* if browser doesn't support the API (older browsers).



### Creating Workers from Inline Code: The Problem

Traditional Web Worker:
```javascript
const worker = new Worker('worker.js'); // Requires separate file
```

*Issue:* For a single-file demo, we can't reference external files.

### The Solution: Blob URLs

```javascript
const workerCode = `
    // Worker code as a string
    self.onmessage = function(e) {
        // Handle messages
    };
`;

const blob = new Blob([workerCode], { type: 'application/javascript' });
const workerUrl = URL.createObjectURL(blob);
const worker = new Worker(workerUrl);
```

*How it works:*
1. *String literal* contains entire worker code
2. *Blob* creates an in-memory file
3. *createObjectURL* creates a temporary URL (blob:http://...)
4. *Worker* loads from that URL
5. *revokeObjectURL* cleans up after workers are created

### Inline Template Literal

```javascript
const workerCode = `
    class Vector { /* ... */ }
    function traceRay(x, y, time) { /* ... */ }
    self.onmessage = function(e) { /* ... */ };
`;
```

*Entire raytracing engine* is embedded as a string inside the main HTML.

*Advantages:*
- Single-file distribution
- Easy to edit and maintain
- No server/CORS issues

*Disadvantages:*
- Syntax highlighting may be limited
- Code duplication if shared logic
- Harder to debug (line numbers off)



### Message Passing Architecture: Communication Protocol

Workers and main thread communicate via *structured messages*:

```javascript
// Main → Worker
worker.postMessage({
    type: 'render',
    data: {
        startY: 0,
        endY: 100,
        width: 400,
        height: 400,
        time: 1234.5,
        frameId: 42
    }
});

// Worker → Main
self.postMessage({
    type: 'slice',
    data: {
        imageData: [/* pixel data */],
        startY: 0,
        endY: 100,
        frameId: 42
    }
});
```

### Message Types

*Main → Worker:*
1. *`init`*--Initial configuration and texture
2. *`render`*--Render a horizontal slice
3. *`updateTexture`*--New texture loaded

*Worker → Main:*
1. *`ready`*--Worker initialized
2. *`slice`*--Rendered slice complete

### Worker Message Handler

```javascript
self.onmessage = function(e) {
    const { type, data } = e.data;
    
    switch (type) {
        case 'init':
            config = data.config;
            textureImage = data.textureImage;
            self.postMessage({ type: 'ready' });
            break;
            
        case 'render':
            const result = processSlice(/* ... */);
            self.postMessage({ type: 'slice', data: result });
            break;
            
        case 'updateTexture':
            textureImage = data.textureImage;
            break;
    }
};
```

*Pattern:*
- Receive message with `type` discriminator
- Extract `data` payload
- Switch on type
- Process and respond



### Work Distribution Strategy: Horizontal Slicing

The image is divided into *horizontal strips*, one per worker:

```
┌─────────────┐ / Worker 0: rows 0-99
├─────────────┤ / Worker 1: rows 100-199
├─────────────┤ / Worker 2: rows 200-299
├─────────────┤ / Worker 3: rows 300-399
└─────────────┘
```

### Slice Calculation

```javascript
const sliceHeight = Math.ceil(HEIGHT / NUM_WORKERS);

for (let i = 0; i < NUM_WORKERS; i++) {
    const startY = i * sliceHeight;
    const endY = Math.min(startY + sliceHeight, HEIGHT);
    
    workers[i].postMessage({
        type: 'render',
        data: { startY, endY, width: WIDTH, height: HEIGHT, time, frameId }
    });
}
```

*Example (4 workers, 400px height):*
- `sliceHeight = ceil(400 / 4) = 100`
- Worker 0: startY=0, endY=100
- Worker 1: startY=100, endY=200
- Worker 2: startY=200, endY=300
- Worker 3: startY=300, endY=400

### Worker Processing

```javascript
function processSlice(startY, endY, width, height, time, frameId) {
    const sliceHeight = endY--startY;
    const sliceData = new Uint8ClampedArray(sliceHeight * width * 4);
    
    for (let y = startY; y < endY; y++) {
        for (let x = 0; x < width; x++) {
            const pixelIndex = ((y--startY) * width + x) * 4;
            const color = traceRay(x, y, time, width, height);
            
            sliceData[pixelIndex] = color[0];
            sliceData[pixelIndex + 1] = color[1];
            sliceData[pixelIndex + 2] = color[2];
            sliceData[pixelIndex + 3] = 255;
        }
    }
    
    return { imageData: sliceData, startY, endY, frameId };
}
```

*Note:* `y--startY` converts global y to local slice y coordinate.

### Why Horizontal Slices?

*Advantages:*
- Simple to implement
- Even load distribution
- Cache-friendly (rows are contiguous in memory)

*Alternatives:*
- *Vertical slices*: Same benefits
- *Tiles*: 2D grid (100×100 blocks)--better for uneven scenes
- *Scanlines*: One row per worker--extreme granularity, high overhead
- *Morton order*: Z-curve pattern--advanced cache optimization



### Frame Management System: The Challenge

Workers complete at *different times*:
- Some slices render faster (simple background)
- Some slices slower (complex reflections)
- Frames can arrive out of order

### Pending Frames Map

```javascript
let pendingFrames = new Map();
```

*Key:* frameId (sequential number)
*Value:* frame information object

```javascript
const frameInfo = {
    imageData: ctx.createImageData(WIDTH, HEIGHT),  // Final composite
    completedSlices: 0                              // Counter
};
pendingFrames.set(frameId, frameInfo);
```

### Slice Reassembly

```javascript
function handleSliceComplete(sliceData) {
    const { imageData, startY, endY, frameId } = sliceData;
    
    if (!pendingFrames.has(frameId)) {
        return; // Frame was abandoned
    }
    
    const frameInfo = pendingFrames.get(frameId);
    frameInfo.completedSlices++;
    
    // Copy slice data to main image
    const mainImageData = frameInfo.imageData;
    const sliceWidth = WIDTH;
    const sliceHeight = endY--startY;
    
    for (let y = 0; y < sliceHeight; y++) {
        for (let x = 0; x < sliceWidth; x++) {
            const srcIndex = (y * sliceWidth + x) * 4;
            const dstIndex = ((startY + y) * WIDTH + x) * 4;
            
            mainImageData.data[dstIndex] = imageData[srcIndex];
            mainImageData.data[dstIndex + 1] = imageData[srcIndex + 1];
            mainImageData.data[dstIndex + 2] = imageData[srcIndex + 2];
            mainImageData.data[dstIndex + 3] = imageData[srcIndex + 3];
        }
    }
    
    // Check if frame is complete
    if (frameInfo.completedSlices === NUM_WORKERS) {
        ctx.putImageData(frameInfo.imageData, 0, 0);
        pendingFrames.delete(frameId);
    }
}
```

*Process:*
1. Slice arrives from worker
2. Check if frame still pending (not abandoned)
3. Copy slice pixels to correct position in frame buffer
4. Increment slice counter
5. When all slices done, display frame and cleanup

### Frame Abandonment

```javascript
// Clean up old frames if too many are pending
if (pendingFrames.size > 3) {
    const oldestFrame = Math.min(...pendingFrames.keys());
    pendingFrames.delete(oldestFrame);
}
```

*Why abandon frames?*
- If rendering is slow, frames pile up
- Displaying old frames causes lag
- Better to skip to newest frame

*Strategy:*
- Keep only 3 most recent frames
- Delete oldest if queue grows
- Workers might finish abandoned frames (ignored)



### Initialisation Sequence: Step-by-Step Startup

```
1. Page loads
   v
2. Create worker blob URL
   v
3. Spawn NUM_WORKERS workers
   v
4. Send 'init' message to each worker
   ├─ Scene configuration
   └─ Texture data (if any)
   v
5. Workers process init
   ├─ Store config
   ├─ Store texture
   └─ Send 'ready' message
   v
6. Main thread waits for all 'ready' messages
   v
7. When workersReady === NUM_WORKERS
   v
8. Start animation loop
```

### Worker Initialization

```javascript
function initializeWorkers() {
    const blob = new Blob([workerCode], { type: 'application/javascript' });
    const workerUrl = URL.createObjectURL(blob);
    
    for (let i = 0; i < NUM_WORKERS; i++) {
        const worker = new Worker(workerUrl);
        worker.onmessage = handleWorkerMessage;
        workers.push(worker);
        
        worker.postMessage({
            type: 'init',
            data: {
                config: SCENE_CONFIG,
                textureImage: textureData
            }
        });
    }
    
    URL.revokeObjectURL(workerUrl); // Clean up blob URL
}
```

### Ready Tracking

```javascript
let workersReady = 0;

function handleWorkerMessage(e) {
    const { type, data } = e.data;
    
    switch (type) {
        case 'ready':
            workersReady++;
            if (workersReady === NUM_WORKERS) {
                console.log(`Initialized ${NUM_WORKERS} workers`);
                requestAnimationFrame(animate);
            }
            break;
        // ...
    }
}
```

*Why wait?*
- Workers need config before rendering
- Sending render commands to uninitialized worker = error
- Synchronization ensures clean startup



### Texture Update Broadcasting: The Challenge

When user uploads new texture:
- Main thread loads image
- All workers need updated texture
- Must happen while rendering

### Broadcast Pattern

```javascript
textureInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    // ... load image ...
    textureData = tempCtx.getImageData(0, 0, img.width, img.height);
    
    // Update all workers
    workers.forEach(worker => {
        worker.postMessage({
            type: 'updateTexture',
            data: { textureImage: textureData }
        });
    });
});
```

*Process:*
1. User selects file
2. Main thread loads and processes image
3. Extract ImageData
4. Send to *all workers simultaneously*
5. Workers update their texture reference
6. Next frame uses new texture

### No Synchronization Needed

*Why it just works:*
- Workers process messages in order
- Texture update arrives before next render
- Even if mid-frame, next frame will be correct
- No need to wait for confirmation

## Performance Monitoring

### FPS Counter

```javascript
let frameCount = 0;
let lastFpsUpdate = 0;

function updateFPS() {
    frameCount++;
    const now = performance.now();
    
    if (now--lastFpsUpdate >= 1000) {
        const fps = Math.round((frameCount * 1000) / (now--lastFpsUpdate));
        fpsDisplay.textContent = `FPS: ${fps}`;
        frameCount = 0;
        lastFpsUpdate = now;
    }
}
```

*Triggered* when frame completes (all slices assembled).

*Calculation:*
- Count frames over ~1 second
- Calculate FPS = frames / seconds
- Update display
- Reset counter

### Performance Comparison

*Single-threaded (spinning_bounce.html):*
- FPS: ~8-15
- CPU: 25% (1 core)
- Frame time: ~70ms

*Multi-threaded (workers.html):*
- FPS: ~30-60
- CPU: 100% (4 cores)
- Frame time: ~20ms

*Speedup:* 3-4× on quad-core system (near-linear scaling)



### Memory Considerations: Data Copying

*Messages copy data* by default:

```javascript
worker.postMessage({ imageData: largeArray }); // Copies entire array
```

*Cost:*
- 400×400×4 bytes = 640KB per slice
- 4 workers × 640KB = 2.56MB per frame
- At 30 FPS = 76.8 MB/s of copying

### Transferable Objects

*Not used in this demo*, but available:

```javascript
worker.postMessage(
    { imageData: arrayBuffer },
    [arrayBuffer]  // Transfer ownership
);
```

*Effect:*
- Zero-copy transfer
- Sender loses access to data
- Much faster for large data

*Why not used here:*
- ImageData can't be transferred directly
- Would need manual ArrayBuffer management
- Complexity not worth it for this demo size

### Memory Per Worker

Each worker has:
- *Code*: ~10KB (raytracing functions)
- *Config*: ~1KB (scene parameters)
- *Texture*: ~1-4MB (uploaded image)
- *Stack/temp*: ~100KB (during rendering)

*Total:* ~2-6 MB per worker × 4 workers = *8-24 MB*

Negligible for modern systems, but considerate for mobile.

## Worker Lifecycle

### Creation

```javascript
const worker = new Worker(workerUrl);
```

- Spawns new thread
- Loads and executes code
- Isolated context created

### Communication

```javascript
worker.onmessage = handleWorkerMessage;
worker.postMessage({ type: 'render', data: { /* ... */ } });
```

- Asynchronous message passing
- Structured clone algorithm
- No shared memory

### Termination

*Not implemented* in this demo (workers live forever).

*Proper cleanup:*
```javascript
workers.forEach(worker => worker.terminate());
workers = [];
```

Should be done:
- On page unload
- When switching scenes
- On error/reset



### Error Handling: Worker Errors

```javascript
worker.onerror = function(error) {
    console.error('Worker error:', error.message, error.filename, error.lineno);
};
```

*Common errors:*
- Undefined variable in worker code
- Division by zero in raytracing
- Invalid message format

### Missing Error Handling

*This demo lacks:*
- Try-catch in worker code
- Error message type
- Graceful degradation to single-threaded

*Production code should:*
- Catch exceptions in worker
- Report errors to main thread
- Fall back to single-threaded mode if workers fail



### Limitations and Trade-offs: Worker Overhead

*Costs:*
- Thread creation: ~10ms
- Message serialization: ~1-2ms per message
- Context switches: minimal but non-zero

*Worth it when:*
- Work is substantial (>10ms per task)
- Work is parallelizable
- Not memory-bound

### Not Always Faster

*Workers won't help when:*
- *Memory-bound*: RAM bandwidth is bottleneck
- *I/O-bound*: Waiting on network/disk
- *Coordination overhead*: Too much synchronization
- *Small tasks*: Message overhead exceeds work

### This Demo's Sweet Spot

*Why it works well:*
- *CPU-bound*: Pure computation (raytracing)
- *Independent tasks*: Slices don't need coordination
- *Large tasks*: Each slice is ~10-20ms of work
- *No shared state*: Only read-only config/texture

*Result:* Near-linear speedup with core count

### Key Differences from Single-threaded

| Aspect | Single-threaded | Multi-threaded |
|--------|-----------------|----------------|
| *Architecture* | Direct function call | Message passing |
| *Rendering* | Sequential loop | Parallel slices |
| *Performance* | 8-15 FPS | 30-60 FPS |
| *CPU usage* | 25% (1 core) | 100% (all cores) |
| *Complexity* | Simple | Frame management |
| *Latency* | Immediate | Async (1-2 frames) |
| *Memory* | Single copy | Multiple copies |
| *Debugging* | Easy | Harder (async) |



### When to Use Web Workers: Good Use Cases

- `+` *Raytracing*--CPU-intensive, parallelizable
- `+` *Image processing*--filters, transformations
- `+` *Physics simulation*--particle systems, cloth
- `+` *Data processing*--parsing, analysis, compression
- `+` *Cryptography*--hashing, encryption
- `+` *AI/ML*--inference, training
- `+` *Audio synthesis*--DSP, effects

### Poor Use Cases

- `-` *DOM manipulation*--can't access DOM from worker
- `-` *Quick tasks*--overhead exceeds benefit
- `-` *Sequential algorithms*--can't parallelize
- `-` *Small datasets*--message copying too expensive
- `-` *Shared mutable state*--workers are isolated

