Pygit is a simpler version of Git (version control system)

First, clone the repo into your machine

```bash
git clone https://github.com/ouzaamohammed/pygit
cd pygit
```

If you want to try Pygit, I recommand installing Pygit in development mode. Run the following command in the root directory of the project

```bash
python3 setup.py develop --user
```

```bash
cd project
pygit init
```

Git should print the following message

```bash
Initialized empty Pygit repository in /home/user/project/.pygit/
```

Pygit works exactly like Git

You stage files using ```add``` command

```bash
pygit add file1 file2
```

You can commit new changes using ```commit``` command

```bash
pygit commit -m 'added file1 and file2'
```


