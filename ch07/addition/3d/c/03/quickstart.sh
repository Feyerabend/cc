#!/bin/bash
# Quick start script for OBJ animation generation

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== OBJ to Animated GIF - Quick Start ===${NC}\n"

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: ./quickstart.sh <obj_file> [frames] [duration_ms]"
    echo ""
    echo "Examples:"
    echo "  ./quickstart.sh model.obj              # Use defaults (36 frames, 100ms)"
    echo "  ./quickstart.sh teapot.obj 60          # 60 frames, 100ms"
    echo "  ./quickstart.sh cube.obj 48 50         # 48 frames, 50ms (faster)"
    echo ""
    exit 1
fi

OBJ_FILE="$1"
FRAMES="${2:-36}"
DURATION="${3:-100}"
BASE_NAME=$(basename "$OBJ_FILE" .obj)
OUTPUT_PREFIX="${BASE_NAME}_frame"
OUTPUT_GIF="${BASE_NAME}_animation.gif"

# Check if OBJ file exists
if [ ! -f "$OBJ_FILE" ]; then
    echo "Error: File '$OBJ_FILE' not found!"
    exit 1
fi

# Build if needed
if [ ! -f "./obj_animator" ]; then
    echo -e "${GREEN}Building obj_animator...${NC}"
    make
    echo ""
fi

# Clean old frames
echo -e "${GREEN}Cleaning old frames...${NC}"
rm -f ${OUTPUT_PREFIX}_*.pam
echo ""

# Generate frames
echo -e "${GREEN}Generating $FRAMES animation frames...${NC}"
./obj_animator "$OBJ_FILE" "$OUTPUT_PREFIX" "$FRAMES" 800 600
echo ""

# Create GIF
echo -e "${GREEN}Creating animated GIF...${NC}"
python3 pam_to_gif.py "${OUTPUT_PREFIX}_*.pam" "$OUTPUT_GIF" "$DURATION" 0
echo ""

# Show result
if [ -f "$OUTPUT_GIF" ]; then
    SIZE=$(du -h "$OUTPUT_GIF" | cut -f1)
    echo -e "${GREEN}✓ Success!${NC}"
    echo -e "  Output: ${BLUE}$OUTPUT_GIF${NC}"
    echo -e "  Size: $SIZE"
    echo -e "  Frames: $FRAMES"
    echo -e "  Duration: ${DURATION}ms per frame"
    echo ""
    echo "Open $OUTPUT_GIF to view your animation!"
else
    echo "Error: Failed to create GIF"
    exit 1
fi
