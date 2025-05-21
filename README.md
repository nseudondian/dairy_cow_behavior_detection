**Cow Monitoring System Setup Guide**

**Introduction:**
This guide provides step-by-step instructions to set up and run the endpoints and front-end of the Cow Monitoring System.

**Prerequisites:**
- Git installed on your system
- Docker installed on your system

**Step 1: Clone the Repository**
```bash
git clone https://gitlab.com/Mujeeb07/cow-detection.git
cd cow-detection
git checkout React-website
```

**Step 2: Build Docker Containers**

**2.1 Front-End Docker Container**
```bash
cd Front-End
docker build -t cowfront:1.0.0 .
```

**2.2 Endpoints Docker Container**
```bash
cd ../Backend
docker build -t cowapi:1.0.0 .
```

**Step 3: Start the Containers**

**3.1 Start Front-End Container**
```bash
docker run -p 3000:3000 cowfront:1.0.0 
```

**3.2 Start Endpoints Container**
```bash
cd ../Backend
docker run -p 5000:5000 -v ./Database:/app/Database/ --gpus all cowapi:1.0.0
```

Now you can access dashboard at ***localhost:3000***