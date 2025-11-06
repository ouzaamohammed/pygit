# pygit  
*A simpler version of Git (version control system)*

## Table of Contents  
- [Overview](#overview)  
- [Features](#features)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Installation](#installation)  
  - [Basic Usage](#basic-usage)  

---

## Overview  
**pygit** is a minimal, easy-to-use version control tool inspired by Git.  
The idea is to provide the core functionalities of Git (`init`, `add`, `commit`, etc.) in a simplified, lightweight implementation — perfect for learning or small projects.

---

## Features  
- 🧱 `pygit init` – initialize a new repository  
- ➕ `pygit add <files>` – stage files for commit  
- 💾 `pygit commit -m "<message>"` – commit staged changes  
- Mirrors the basic workflow of Git in a simplified environment  
- Written in pure Python — easy to read, understand, and extend  

---

## Getting Started  

### Prerequisites  
- Python 3.x  
- Basic familiarity with the command line  

### Installation  
Clone the repository and install in development mode so changes are reflected immediately:  

```bash
git clone https://github.com/ouzaamohammed/pygit.git  
cd pygit  
python3 setup.py develop --user  
```

```bash
cd /path/to/your/project  
pygit init  
# -> Initialized empty Pygit repository in …/.pygit/

pygit add file1.txt file2.txt  
pygit commit -m "Added file1 and file2"
```


