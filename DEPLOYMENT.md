# F-OSINT DWv1 - Deployment Guide

## Overview

F-OSINT DWv1 is a comprehensive Dark Web OSINT and Analysis tool developed by 4p0ca1ypse. This guide will help you deploy and run the application.

## System Requirements

- Python 3.8 or higher
- Tor Browser or Tor service (for dark web functionality)
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection

### Operating System Support
- Linux (Ubuntu 20.04+, Debian 10+, CentOS 7+)
- Windows 10/11
- macOS 10.15+

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/4p0ca1ypse3/F-OSINT-v1.git
cd F-OSINT-v1
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tor python3-pyqt5 libqt5core5a libqt5gui5 libqt5widgets5
```

#### CentOS/RHEL:
```bash
sudo yum install tor PyQt5 qt5-qtbase
```

#### Windows:
- Download and install Tor Browser from https://www.torproject.org/
- Python dependencies will be installed via pip

#### macOS:
```bash
brew install tor
# Python dependencies will be installed via pip
```

## Configuration

### 1. Tor Setup

The application requires Tor for dark web functionality. You can either:

**Option A: Use Tor Browser (Recommended for beginners)**
- Download and install Tor Browser
- Start Tor Browser before running F-OSINT DWv1

**Option B: Run Tor as a service**
```bash
# Ubuntu/Debian
sudo systemctl start tor
sudo systemctl enable tor

# macOS
brew services start tor
```

### 2. Application Configuration

Configuration files are located in the `config/` directory:

- `settings.json`: Main application settings
- `tor_config.txt`: Tor-specific configuration

You can modify these files to customize the application behavior.

## Running the Application

### Start F-OSINT DWv1

```bash
cd F-OSINT-v1
python src/main.py
```

### First Time Setup

1. **User Registration**: Create your first user account
2. **Tor Connection**: Ensure Tor is running and connect
3. **Create Project**: Start your first OSINT investigation

## Features Overview

### 🔍 Core OSINT Modules

- **Dark Web Scanner**: Automated .onion site crawling and analysis
- **Google Dorking**: Advanced search queries with custom operators
- **Leak Checker**: Email/username/phone breach verification
- **PGP Key Search**: Cryptographic key discovery across key servers
- **Crypto Tracker**: Cryptocurrency address analysis (BTC, ETH)
- **Metadata Extractor**: File metadata analysis and privacy assessment
- **Keyword Alerts**: Real-time monitoring and alerting system

### 🛡️ Security Features

- **User Authentication**: Secure sign-up/sign-in with encrypted passwords
- **Session Management**: Encrypted session storage and management
- **Tor Integration**: All dark web queries routed through Tor network
- **Data Encryption**: Sensitive data encrypted using industry standards

### 📊 Reporting & Management

- **PDF Reports**: Professional investigation reports
- **Markdown Reports**: Human-readable investigation summaries
- **Project Management**: Organize investigations with auto-save
- **Session Persistence**: Resume work across application restarts

### 🎨 User Interface

- **Modern GUI**: Built with PyQt5 for responsive user experience
- **Light/Dark Themes**: Switch between visual themes
- **Tabbed Interface**: Organized modules and easy navigation
- **Real-time Status**: Live updates on Tor connection and operations

## Usage Examples

### Basic Investigation Workflow

1. **Create Project**: Start a new investigation
2. **Add Targets**: Define domains, emails, or other targets
3. **Run Scans**: Use various OSINT modules to gather intelligence
4. **Analyze Results**: Review findings and add notes
5. **Generate Reports**: Export professional reports in PDF/Markdown

### Advanced Features

- **Bulk Operations**: Process multiple targets simultaneously
- **Automated Monitoring**: Set up keyword alerts for ongoing surveillance
- **Data Correlation**: Cross-reference findings across different modules
- **Privacy Analysis**: Assess privacy risks in collected data

## Troubleshooting

### Common Issues

**Tor Connection Failed**
```
Solution: Ensure Tor is running on localhost:9050
Check: sudo systemctl status tor
```

**PyQt5 Import Error**
```
Solution: Install Qt5 development packages
Ubuntu: sudo apt install python3-pyqt5-dev
```

**Permission Denied Errors**
```
Solution: Run with appropriate permissions
Check: chmod +x src/main.py
```

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export FOSINT_DEBUG=1
python src/main.py
```

## Security Considerations

### Operational Security (OpSec)

1. **Use VPN**: Consider using VPN in addition to Tor
2. **Isolated Environment**: Run in virtual machine when possible
3. **Regular Updates**: Keep all dependencies updated
4. **Data Handling**: Securely store and dispose of sensitive data

### Legal Compliance

- Ensure compliance with local laws and regulations
- Obtain proper authorization before investigating targets
- Respect terms of service of external services
- Use only for legitimate security research and education

## API Integration

F-OSINT DWv1 supports integration with external APIs:

- **Have I Been Pwned**: Breach checking (API key required)
- **VirusTotal**: File and URL analysis (API key optional)
- **Shodan**: Network device discovery (API key optional)

Configure API keys in `config/settings.json`:
```json
{
  "apis": {
    "haveibeenpwned": "your-api-key",
    "virustotal": "your-api-key",
    "shodan": "your-api-key"
  }
}
```

## Performance Optimization

### System Tuning

1. **Increase RAM**: More RAM allows for larger datasets
2. **SSD Storage**: Faster disk I/O improves performance
3. **Network Bandwidth**: Higher bandwidth for faster data collection

### Application Tuning

1. **Adjust Rate Limits**: Modify request rates in settings
2. **Optimize Database**: Regular cleanup of old data
3. **Monitor Resources**: Use system monitoring tools

## Backup and Recovery

### Data Backup

Important directories to backup:
- `data/`: User accounts and projects
- `config/`: Application configuration
- `reports/`: Generated reports

### Automated Backup

Create backup script:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "fosint_backup_$DATE.tar.gz" data/ config/ reports/
```

## Contributing

### Development Setup

1. Fork the repository
2. Create feature branch
3. Install development dependencies
4. Run tests before submitting PR

### Reporting Issues

- Use GitHub Issues for bug reports
- Include system information and error logs
- Provide steps to reproduce the issue

## License

F-OSINT DWv1 is released under the MIT License. See LICENSE file for details.

## Support

For support and updates:
- GitHub: https://github.com/4p0ca1ypse3/F-OSINT-v1
- Developer: 4p0ca1ypse (ApocalypseYetAgain)

---

**Disclaimer**: This tool is for educational and legitimate research purposes only. Users are responsible for complying with applicable laws and regulations.