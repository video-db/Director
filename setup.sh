#!/bin/bash

confirm() {
    # Function to prompt user for confirmation
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
}

install_nvm() {
    # Load nvm if it's already installed
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        . "$NVM_DIR/nvm.sh"
    elif [ -s "$HOME/.nvm/nvm.sh" ]; then
        export NVM_DIR="$HOME/.nvm"
        . "$NVM_DIR/nvm.sh"
    fi

    if ! command -v nvm &> /dev/null; then
        echo "📦 nvm is not installed."
        if confirm "Would you like to install nvm?"; then
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

            # Load nvm to current shell session
            export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm

            echo "✅ nvm has been successfully installed!"
        else
            echo "⏭️ Skipping nvm installation."
        fi
    else
        echo "✅ nvm is already installed."
    fi
}

install_node_with_nvm() {
    # Ensure nvm is loaded
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        . "$NVM_DIR/nvm.sh"
    elif [ -s "$HOME/.nvm/nvm.sh" ]; then
        export NVM_DIR="$HOME/.nvm"
        . "$NVM_DIR/nvm.sh"
    fi

    if ! command -v nvm &> /dev/null; then
        echo "❌ nvm is not installed. Please install nvm first."
        return 1
    fi

    # Determine the Node.js version to install
    if [ -z "$1" ]; then
        # Default to latest LTS version if no version is provided
        node_version=$(nvm ls-remote --lts | tail -1 | awk '{print $1}')
    else
        # Use the provided version
        node_version="$1"
    fi

    installed_node=$(nvm ls --no-colors | grep -w "v$node_version")

    if [ -n "$installed_node" ]; then
        echo "✅ Node.js version $node_version is already installed."
        nvm use $node_version
    else
        if confirm "Would you like to install Node.js version $node_version using nvm?"; then
            nvm install $node_version
            nvm use $node_version
            echo "✅ Node.js $node_version and npm have been successfully installed with nvm!"
        else
            echo "⏭️ Skipping Node.js installation."
        fi
    fi
}

detect_package_manager() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            echo "apt"
        elif command -v yum &> /dev/null; then
            echo "yum"
        elif command -v dnf &> /dev/null; then
            echo "dnf"
        elif command -v pacman &> /dev/null; then
            echo "pacman"
        elif command -v zypper &> /dev/null; then
            echo "zypper"
        else
            echo "❌ Unsupported Linux package manager"
            return 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            echo "brew"
        else
            echo "❌ Homebrew is not installed"
            return 1
        fi
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "❌ Windows detected. Please install dependencies manually."
        return 1
    else
        echo "❌ Unsupported OS"
        return 1
    fi
}

install_dependency() {
    local package_manager=$1
    local dependency=$2

    if ! command -v $dependency &> /dev/null; then
        echo "📦 $dependency is not installed."
        if confirm "Would you like to install $dependency using $package_manager?"; then
            case $package_manager in
                apt)
                    sudo apt update && sudo apt install -y $dependency
                    ;;
                yum)
                    sudo yum install -y $dependency
                    ;;
                dnf)
                    sudo dnf install -y $dependency
                    ;;
                pacman)
                    sudo pacman -S --noconfirm $dependency
                    ;;
                zypper)
                    sudo zypper install -y $dependency
                    ;;
                brew)
                    export HOMEBREW_NO_AUTO_UPDATE=1
                    brew install $dependency
                    ;;
                *)
                    echo "❌ Unsupported package manager"
                    return 1
                    ;;
            esac
            echo "✅ $dependency has been successfully installed!"
        else
            echo "⏭️ Skipping $dependency installation."
        fi
    else
        echo "✅ $dependency is already installed."
    fi
}

install_python_and_pip() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
        REQUIRED_VERSION="3.9"

        # Check if Python version is at least 3.9
        if [[ $(echo -e "$PYTHON_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) == "$REQUIRED_VERSION" ]]; then
            echo "✅ Python 3 (version $PYTHON_VERSION) is already installed and meets the required version."
            return 0
        else
            echo "❌ Current Python version ($PYTHON_VERSION) is less than the required 3.9, trying to upgrade it.."
        fi
    else
        echo "❌ Python 3 is not installed."
    fi
    echo "⚙️ Attempting to install Python 3.9 or higher..."
    package_manager=$(detect_package_manager)
    if [ $? -eq 0 ]; then
        case $package_manager in
            apt)
                # For Debian/Ubuntu
                sudo apt update
                sudo apt install -y python3 python3-pip python3-venv
                ;;
            yum)
                # For CentOS/RHEL
                sudo yum install -y python3 python3-pip python3-virtualenv
                ;;
            dnf)
                # For Fedora
                sudo dnf install -y python3 python3-pip python3-virtualenv
                ;;
            pacman)
                # For Arch Linux
                sudo pacman -Sy --noconfirm python python-pip python-virtualenv
                ;;
            zypper)
                # For OpenSUSE
                sudo zypper install -y python3 python3-pip python3-virtualenv
                ;;
            brew)
                # For macOS using Homebrew
                export HOMEBREW_NO_AUTO_UPDATE=1
                brew install python
                ;;
            *)
                echo "❌ Unsupported package manager: $package_manager"
                return 1
                ;;
        esac
        echo "✅ Python 3, pip, and virtual environment packages have been successfully installed!"
    else
        echo "❌ Package manager detection failed: $package_manager"
    fi

    # Check for pip and venv separately as they might not be included with Python
    if ! command -v pip3 &> /dev/null; then
        echo "📦 pip3 is not installed. Installing..."
        install_dependency $package_manager python3-pip
    fi

    if ! python3 -m venv --help &> /dev/null; then
        echo "📦 venv module is not installed. Installing..."
        install_dependency $package_manager python3-venv
    fi
}

check_and_install_dependencies() {
    install_nvm
    install_node_with_nvm 22.8.0
    install_python_and_pip
}

# Call the function to start the installation process
check_and_install_dependencies

# Ensure PATH is updated
export PATH="$HOME/.local/bin:$PATH"

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel

echo "
🐍 Using Python: $(which python3)"
echo "🐍 Using pip: $(which pip3)"

echo "
🔧 Let's set up your environment. You can skip this step and add it to .env later."

echo "🔑 VideoDB API Key (https://console.videodb.io/) (Press Enter to skip)"
read VIDEO_DB_API_KEY

# Create a .env file and add the content
echo "📝 Creating .env file with provided API keys..."
cat <<EOT > .env
VIDEO_DB_API_KEY=$VIDEO_DB_API_KEY
EOT
cd ..

make install-be
make init-sqlite-db

# Frontend setup
cd frontend

echo "
🌳 Using Node@$(node -v): $(which node)"
echo "🌳 Using npm@$(npm -v): $(which npm)"

cat <<EOT > .env
VITE_APP_BACKEND_URL=http://127.0.0.1:8000
VITE_PORT=8080
VITE_OPEN_BROWSER=true
EOT
cd ../

make install-fe
make update-fe

echo "
*******************************************
*                                         *
*   🎉 Setup Completed Successfully! 🎉   *
*                                         *
*      🚀 IMPORTANT: Next Steps 🚀        *
*                                         *
* 1. Review and Update .env File:         *
*    - Check the newly created .env file  *
*    - Add VIDEO_DB_API_KEY               *
*                                         *
* 2. Start the Application:               *
*    Run the following command:           *
*    $ make run                           *
*                                         *
*   🎉 You're all set! Happy coding! 🎉    *
*                                         *
*******************************************
"