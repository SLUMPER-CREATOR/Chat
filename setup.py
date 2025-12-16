from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="django-chat-app",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Modern real-time chat application built with Django and WebSocket",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/django-chat",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Django",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 6.0",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    keywords="django, chat, websocket, real-time, messaging",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/django-chat/issues",
        "Source": "https://github.com/yourusername/django-chat",
        "Documentation": "https://github.com/yourusername/django-chat#readme",
    },
)