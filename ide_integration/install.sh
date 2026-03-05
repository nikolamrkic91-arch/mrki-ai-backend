#!/bin/bash

# Mrki IDE Integration Installation Script
# Installs all IDE integrations and CLI tools

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_LOG="/tmp/mrki-install.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[Mrki]${NC} $1" | tee -a "$INSTALL_LOG"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$INSTALL_LOG"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$INSTALL_LOG"
}

error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$INSTALL_LOG"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    success "Python $PYTHON_VERSION found"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed"
        exit 1
    fi
    success "pip3 found"
    
    # Check Node.js (for VS Code extension)
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            success "Node.js $(node --version) found"
        else
            warning "Node.js 18+ recommended (found $(node --version))"
        fi
    else
        warning "Node.js not found - VS Code extension cannot be built"
    fi
    
    # Check Rust (for Zed extension)
    if command -v rustc &> /dev/null; then
        success "Rust $(rustc --version) found"
    else
        warning "Rust not found - Zed extension cannot be built"
    fi
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    
    pip3 install --user rich requests click pydantic watchdog 2>&1 | tee -a "$INSTALL_LOG"
    
    success "Python dependencies installed"
}

# Install CLI
install_cli() {
    log "Installing Mrki CLI..."
    
    cd "$SCRIPT_DIR/cli"
    
    # Create mrki command
    mkdir -p ~/.local/bin
    
    cat > ~/.local/bin/mrki << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, "SCRIPT_DIR")
from mrki import main
if __name__ == "__main__":
    main()
EOF
    sed -i "s|SCRIPT_DIR|$SCRIPT_DIR|g" ~/.local/bin/mrki
    chmod +x ~/.local/bin/mrki
    
    success "CLI installed to ~/.local/bin/mrki"
}

# Install LSP
install_lsp() {
    log "Installing Mrki Language Server..."
    
    mkdir -p ~/.local/bin
    
    cat > ~/.local/bin/mrki-lsp << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, "SCRIPT_DIR")
from lsp.server import main
if __name__ == "__main__":
    main()
EOF
    sed -i "s|SCRIPT_DIR|$SCRIPT_DIR|g" ~/.local/bin/mrki-lsp
    chmod +x ~/.local/bin/mrki-lsp
    
    success "LSP server installed to ~/.local/bin/mrki-lsp"
}

# Install DAP
install_dap() {
    log "Installing Mrki Debug Adapter..."
    
    mkdir -p ~/.local/bin
    
    cat > ~/.local/bin/mrki-dap << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, "SCRIPT_DIR")
from dap.server import main
if __name__ == "__main__":
    main()
EOF
    sed -i "s|SCRIPT_DIR|$SCRIPT_DIR|g" ~/.local/bin/mrki-dap
    chmod +x ~/.local/bin/mrki-dap
    
    success "DAP server installed to ~/.local/bin/mrki-dap"
}

# Install VS Code extension
install_vscode() {
    log "Installing VS Code extension..."
    
    if ! command -v code &> /dev/null; then
        warning "VS Code not found, skipping"
        return
    fi
    
    cd "$SCRIPT_DIR/vscode"
    
    if [ ! -d "node_modules" ]; then
        log "Installing Node.js dependencies..."
        npm install 2>&1 | tee -a "$INSTALL_LOG"
    fi
    
    log "Compiling TypeScript..."
    npm run compile 2>&1 | tee -a "$INSTALL_LOG"
    
    log "Packaging extension..."
    if command -v vsce &> /dev/null; then
        vsce package 2>&1 | tee -a "$INSTALL_LOG"
        code --install-extension mrki-vscode-*.vsix 2>&1 | tee -a "$INSTALL_LOG"
        success "VS Code extension installed"
    else
        warning "vsce not found, installing extension from source..."
        code --install-extension . 2>&1 | tee -a "$INSTALL_LOG" || warning "Could not install VS Code extension"
    fi
}

# Install Cursor extension
install_cursor() {
    log "Installing Cursor extension..."
    
    if ! command -v cursor &> /dev/null; then
        warning "Cursor not found, skipping"
        return
    fi
    
    cd "$SCRIPT_DIR/cursor"
    
    if [ ! -d "node_modules" ]; then
        log "Installing Node.js dependencies..."
        npm install 2>&1 | tee -a "$INSTALL_LOG"
    fi
    
    log "Compiling TypeScript..."
    npm run compile 2>&1 | tee -a "$INSTALL_LOG"
    
    log "Installing to Cursor..."
    cursor --install-extension . 2>&1 | tee -a "$INSTALL_LOG" || warning "Could not install Cursor extension"
    
    success "Cursor extension installed"
}

# Install Zed extension
install_zed() {
    log "Installing Zed extension..."
    
    if ! command -v zed &> /dev/null; then
        warning "Zed not found, skipping"
        return
    fi
    
    if ! command -v cargo &> /dev/null; then
        warning "Rust/Cargo not found, skipping"
        return
    fi
    
    cd "$SCRIPT_DIR/zed"
    
    log "Building Zed extension..."
    cargo build --release 2>&1 | tee -a "$INSTALL_LOG"
    
    # Copy to Zed extensions directory
    ZED_EXT_DIR="$HOME/.config/zed/extensions"
    mkdir -p "$ZED_EXT_DIR/mrki"
    cp -r extension.toml languages "$ZED_EXT_DIR/mrki/"
    cp target/release/libmrki_zed.dylib "$ZED_EXT_DIR/mrki/" 2>/dev/null || \
    cp target/release/libmrki_zed.so "$ZED_EXT_DIR/mrki/" 2>/dev/null || true
    
    success "Zed extension installed"
}

# Create config directory
setup_config() {
    log "Setting up configuration..."
    
    mkdir -p ~/.mrki
    
    if [ ! -f ~/.mrki/config.json ]; then
        cat > ~/.mrki/config.json << 'EOF'
{
  "server": {
    "host": "localhost",
    "port": 8765
  },
  "completion": {
    "enabled": true,
    "inline": true
  },
  "ui": {
    "theme": "dark",
    "animations": true
  }
}
EOF
        success "Default config created at ~/.mrki/config.json"
    fi
}

# Update PATH
update_path() {
    log "Updating PATH..."
    
    SHELL_RC=""
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
        if ! grep -q "\.local/bin" "$SHELL_RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            success "Updated $SHELL_RC"
        fi
    fi
}

# Print summary
print_summary() {
    echo
    echo "========================================"
    echo -e "${GREEN}Mrki IDE Integration Installed!${NC}"
    echo "========================================"
    echo
    echo "Installed components:"
    echo "  ✓ CLI (mrki)"
    echo "  ✓ Language Server (mrki-lsp)"
    echo "  ✓ Debug Adapter (mrki-dap)"
    
    if command -v code &> /dev/null; then
        echo "  ✓ VS Code Extension"
    fi
    
    if command -v cursor &> /dev/null; then
        echo "  ✓ Cursor Extension"
    fi
    
    if command -v zed &> /dev/null; then
        echo "  ✓ Zed Extension"
    fi
    
    echo
    echo "Quick start:"
    echo "  mrki status       # Check status"
    echo "  mrki init         # Initialize project"
    echo "  mrki chat         # Start chat"
    echo
    echo "For more info: mrki --help"
    echo
    echo "Installation log: $INSTALL_LOG"
    echo
    
    if ! echo "$PATH" | grep -q "\.local/bin"; then
        warning "Please restart your shell or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

# Main installation
main() {
    echo "========================================"
    echo "  Mrki IDE Integration Installer"
    echo "========================================"
    echo
    
    # Clear log
    > "$INSTALL_LOG"
    
    check_prerequisites
    install_python_deps
    install_cli
    install_lsp
    install_dap
    install_vscode
    install_cursor
    install_zed
    setup_config
    update_path
    
    print_summary
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cli-only)
            check_prerequisites
            install_python_deps
            install_cli
            install_lsp
            install_dap
            setup_config
            update_path
            exit 0
            ;;
        --vscode-only)
            install_vscode
            exit 0
            ;;
        --cursor-only)
            install_cursor
            exit 0
            ;;
        --zed-only)
            install_zed
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --cli-only      Install only CLI tools"
            echo "  --vscode-only   Install only VS Code extension"
            echo "  --cursor-only   Install only Cursor extension"
            echo "  --zed-only      Install only Zed extension"
            echo "  --help, -h      Show this help"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
    shift
done

main
