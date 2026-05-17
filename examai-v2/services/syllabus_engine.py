# ============================================================
# services/syllabus_engine.py
# Parses uploaded syllabi (PDF/DOCX/TXT) or manual text.
# Extracts units, topics, subtopics, and keywords.
# ============================================================
import re
import json
import os
from typing import Dict, List, Tuple


# ── Subject knowledge base for fallback/enrichment ────────────
SUBJECT_TOPICS: Dict[str, Dict[str, List[str]]] = {
    "DBMS": {
        "Unit 1: Introduction": ["Database concepts","DBMS architecture","Data models","ER model","Entity and attributes","Relationships","Keys","Constraints"],
        "Unit 2: Relational Model": ["Relational algebra","Selection","Projection","Join","Union","Intersection","Tuple relational calculus","Domain relational calculus"],
        "Unit 3: SQL": ["DDL commands","DML commands","DCL commands","SELECT queries","WHERE clause","GROUP BY","ORDER BY","Joins","Subqueries","Views","Triggers","Stored procedures","Indexes"],
        "Unit 4: Normalization": ["Functional dependencies","1NF","2NF","3NF","BCNF","4NF","5NF","Decomposition","Lossless join","Dependency preservation"],
        "Unit 5: Transactions & Concurrency": ["ACID properties","Transaction states","Concurrency control","Two-phase locking","Deadlock","Serialization","Recovery","Log-based recovery","Checkpoints"],
        "Unit 6: Indexing & Hashing": ["Dense index","Sparse index","B-tree index","B+ tree","Hashing","Static hashing","Dynamic hashing","Extendible hashing"],
    },
    "Python": {
        "Unit 1: Basics": ["Python syntax","Variables","Data types","Operators","Input/Output","Type conversion","String operations","Comments"],
        "Unit 2: Control Structures": ["if-else","elif","for loop","while loop","break","continue","pass","nested loops","List comprehension"],
        "Unit 3: Functions": ["Function definition","Arguments","Return values","Default arguments","*args **kwargs","Lambda functions","Recursion","Scope","Closures","Decorators"],
        "Unit 4: Data Structures": ["Lists","Tuples","Dictionaries","Sets","List methods","Dictionary methods","Stacks","Queues","Linked lists"],
        "Unit 5: OOP": ["Classes","Objects","__init__","Encapsulation","Inheritance","Polymorphism","Abstraction","Method overriding","Multiple inheritance","Abstract classes","Interfaces"],
        "Unit 6: File Handling & Exceptions": ["File open/close","Read/Write","Append mode","with statement","try-except-finally","Custom exceptions","Exception hierarchy","raise statement"],
        "Unit 7: Modules & Libraries": ["import","Standard library","os module","sys module","math module","datetime","random","NumPy basics","Pandas basics","Regular expressions"],
    },
    "AI": {
        "Unit 1: Introduction to AI": ["History of AI","Turing test","Intelligent agents","PEAS framework","Agent types","Environment types","Rationality"],
        "Unit 2: Search Algorithms": ["State space search","BFS","DFS","Uniform cost search","Greedy best-first search","A* algorithm","AO* algorithm","Heuristic functions","Admissibility"],
        "Unit 3: Knowledge Representation": ["Propositional logic","Predicate logic","Inference rules","Semantic networks","Frames","Production rules","Expert systems","Ontologies"],
        "Unit 4: Machine Learning": ["Supervised learning","Unsupervised learning","Reinforcement learning","Decision trees","Naive Bayes","k-NN","Linear regression","Logistic regression","Neural networks","SVM"],
        "Unit 5: Natural Language Processing": ["Tokenization","POS tagging","Parsing","Semantic analysis","Sentiment analysis","Named entity recognition","Language models"],
        "Unit 6: Planning & Uncertainty": ["STRIPS planning","Bayesian networks","Probability theory","Hidden Markov models","Fuzzy logic","Genetic algorithms"],
    },
    "CN": {
        "Unit 1: Introduction": ["Network types","LAN WAN MAN","Network topologies","OSI model","TCP/IP model","Protocol layers","Encapsulation"],
        "Unit 2: Physical & Data Link Layer": ["Transmission media","Bandwidth","Multiplexing","Error detection","Error correction","CRC","Hamming code","Framing","HDLC","PPP","Sliding window"],
        "Unit 3: Network Layer": ["IP addressing","IPv4","IPv6","Subnetting","CIDR","Routing algorithms","Distance vector","Link state","RIP","OSPF","BGP","NAT","ARP","ICMP"],
        "Unit 4: Transport Layer": ["TCP","UDP","Port numbers","TCP connection","Three-way handshake","Flow control","Congestion control","Socket programming"],
        "Unit 5: Application Layer": ["HTTP","HTTPS","FTP","SMTP","POP3","IMAP","DNS","DHCP","Telnet","SSH","SNMP"],
        "Unit 6: Network Security": ["Cryptography","Symmetric encryption","Asymmetric encryption","RSA","DES","AES","Digital signatures","SSL/TLS","Firewalls","VPN","IDS"],
    },
    "OS": {
        "Unit 1: Introduction": ["OS functions","OS types","OS structure","System calls","Kernel","Monolithic","Microkernel","Process concept"],
        "Unit 2: Process Management": ["Process states","PCB","Process scheduling","FCFS","SJF","Round Robin","Priority scheduling","Multilevel queue","Gantt charts","Waiting time","Turnaround time"],
        "Unit 3: Synchronization": ["Race condition","Critical section","Mutex","Semaphores","Monitors","Producer-consumer problem","Readers-writers","Dining philosophers","Deadlock conditions","Deadlock prevention","Deadlock avoidance","Banker's algorithm"],
        "Unit 4: Memory Management": ["Contiguous allocation","Paging","Segmentation","Virtual memory","Demand paging","Page replacement algorithms","FIFO","LRU","Optimal","Thrashing","Working set"],
        "Unit 5: File Systems": ["File concepts","File operations","File types","Directory structure","File allocation","FAT","Inode","Disk scheduling","FCFS","SSTF","SCAN","C-SCAN"],
    },
    "Java": {
        "Unit 1: Basics": ["JVM JRE JDK","Java program structure","Data types","Variables","Operators","Control flow","Arrays","String class"],
        "Unit 2: OOP Concepts": ["Classes","Objects","Constructors","this keyword","static","Encapsulation","Inheritance","super keyword","Method overriding","Polymorphism","Abstraction","Abstract classes","Interfaces"],
        "Unit 3: Exception Handling": ["try-catch-finally","throw throws","Checked exceptions","Unchecked exceptions","Custom exceptions","Exception hierarchy","Multi-catch"],
        "Unit 4: Collections & Generics": ["ArrayList","LinkedList","HashMap","HashSet","TreeMap","Iterator","Generics","Comparable","Comparator","Collections class"],
        "Unit 5: Multithreading": ["Thread class","Runnable interface","Thread lifecycle","synchronization","wait notify","Producer-consumer","Thread pool","Executor framework"],
        "Unit 6: File I/O & Streams": ["FileInputStream","FileOutputStream","BufferedReader","BufferedWriter","ObjectInputStream","Serialization","NIO","Path","Files"],
    },
    "DS": {
        "Unit 1: Arrays & Strings": ["Array operations","2D arrays","String manipulation","Pattern matching","String algorithms"],
        "Unit 2: Linked Lists": ["Singly linked list","Doubly linked list","Circular linked list","Insertion","Deletion","Reversal","Merge","Floyd's algorithm"],
        "Unit 3: Stacks & Queues": ["Stack operations","Applications of stack","Infix postfix prefix","Queue operations","Circular queue","Priority queue","Deque"],
        "Unit 4: Trees": ["Binary tree","BST","Tree traversals","AVL tree","Rotations","Heap","Heapify","Priority queue","B-tree","Trie"],
        "Unit 5: Graphs": ["Graph representation","BFS","DFS","Shortest path","Dijkstra","Bellman-Ford","Minimum spanning tree","Prim","Kruskal","Topological sort"],
        "Unit 6: Sorting & Searching": ["Bubble sort","Selection sort","Insertion sort","Merge sort","Quick sort","Heap sort","Radix sort","Binary search","Hashing","Time complexity","Space complexity"],
    },
    "SE": {
        "Unit 1: Introduction": ["Software process","SDLC","Waterfall model","Spiral model","Agile","Scrum","Kanban","XP","RAD model"],
        "Unit 2: Requirements": ["Requirements engineering","Functional requirements","Non-functional requirements","Use case","SRS document","Requirements elicitation","Validation"],
        "Unit 3: Design": ["System design","Architectural design","Design patterns","Cohesion","Coupling","UML diagrams","Class diagram","Sequence diagram","DFD"],
        "Unit 4: Testing": ["Unit testing","Integration testing","System testing","Acceptance testing","Black box testing","White box testing","Test cases","Code coverage","Regression testing"],
        "Unit 5: Project Management": ["Project planning","COCOMO","Function points","Risk management","Configuration management","Change management","Project scheduling","Gantt chart","PERT"],
    },
    "ML": {
        "Unit 1: Introduction": ["Machine learning overview","Supervised learning","Unsupervised learning","Reinforcement learning","Bias variance tradeoff","Overfitting","Underfitting","Cross validation"],
        "Unit 2: Regression": ["Linear regression","Multiple regression","Polynomial regression","Ridge regression","Lasso","Gradient descent","Cost function","Normal equation"],
        "Unit 3: Classification": ["Logistic regression","Decision tree","Random forest","SVM","Naive Bayes","k-NN","Ensemble methods","Boosting","Bagging"],
        "Unit 4: Clustering": ["K-means","Hierarchical clustering","DBSCAN","Silhouette score","Elbow method","Gaussian mixture"],
        "Unit 5: Neural Networks": ["Perceptron","Multilayer perceptron","Backpropagation","Activation functions","CNN","RNN","LSTM","Transfer learning"],
        "Unit 6: Evaluation": ["Confusion matrix","Precision recall F1","ROC AUC","Mean squared error","Cross entropy","Model selection","Hyperparameter tuning"],
    },
}


# ── File text extractors ───────────────────────────────────────
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        import PyPDF2
        text = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text.append(t)
        return "\n".join(text)
    except Exception as e:
        print(f"[Syllabus] PDF extraction error: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        print(f"[Syllabus] DOCX extraction error: {e}")
        return ""


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Route file to correct extractor."""
    ext = file_type.lower()
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""


# ── Topic / Unit extraction from raw text ─────────────────────
def extract_units_and_topics(raw_text: str, subject: str) -> Dict:
    """
    Parse raw syllabus text into structured units+topics.
    Returns: {units: [...], topics_flat: [...], keywords: [...]}
    """
    lines     = [l.strip() for l in raw_text.splitlines() if l.strip()]
    units     = []
    topics_flat = []
    keywords  = set()
    current_unit = None
    current_unit_topics = []

    # Patterns for unit headers
    unit_patterns = [
        r'^(unit\s*[-:]?\s*\d+[:\s]+)(.*)',
        r'^(module\s*[-:]?\s*\d+[:\s]+)(.*)',
        r'^(\d+\.\s+)(.*)',
        r'^(chapter\s*\d+[:\s]+)(.*)',
    ]

    # Patterns for topic lines
    topic_patterns = [
        r'^\d+\.\d+\s+(.*)',   # 1.1 Topic
        r'^[-•*]\s+(.*)',       # bullet topic
        r'^[a-z]\)\s+(.*)',     # a) topic
    ]

    for line in lines:
        line_lower = line.lower()

        # Check if unit header
        is_unit = False
        for pat in unit_patterns:
            m = re.match(pat, line, re.IGNORECASE)
            if m:
                # Save previous unit
                if current_unit and current_unit_topics:
                    units.append({
                        "unit_name": current_unit,
                        "topics": current_unit_topics
                    })
                current_unit = line
                current_unit_topics = []
                is_unit = True
                break

        if is_unit:
            continue

        # Check if topic line
        for pat in topic_patterns:
            m = re.match(pat, line)
            if m:
                topic = m.group(1).strip()
                if len(topic) > 3:
                    current_unit_topics.append(topic)
                    topics_flat.append(topic)
                    # Extract keywords (words > 4 chars)
                    for word in re.findall(r'\b[A-Za-z]{4,}\b', topic):
                        keywords.add(word.lower())
                break
        else:
            # Plain line: treat as topic if not too long
            if 5 < len(line) < 120 and not line.endswith(":"):
                if current_unit:
                    current_unit_topics.append(line)
                topics_flat.append(line)
                for word in re.findall(r'\b[A-Za-z]{4,}\b', line):
                    keywords.add(word.lower())

    # Append last unit
    if current_unit and current_unit_topics:
        units.append({"unit_name": current_unit, "topics": current_unit_topics})

    # Fallback: if no units parsed, use subject knowledge base
    if not units and subject in SUBJECT_TOPICS:
        for unit_name, unit_topics in SUBJECT_TOPICS[subject].items():
            # Check if any topic text appears in raw_text
            matched = [t for t in unit_topics
                       if any(w.lower() in raw_text.lower()
                              for w in t.split() if len(w) > 3)]
            if matched:
                units.append({"unit_name": unit_name, "topics": matched})
                topics_flat.extend(matched)
                for t in matched:
                    for w in t.split():
                        if len(w) > 3:
                            keywords.add(w.lower())

    # If still empty, use full subject knowledge base
    if not units and subject in SUBJECT_TOPICS:
        for unit_name, unit_topics in SUBJECT_TOPICS[subject].items():
            units.append({"unit_name": unit_name, "topics": unit_topics})
            topics_flat.extend(unit_topics)

    return {
        "units":       units,
        "topics_flat": list(dict.fromkeys(topics_flat)),  # deduplicated
        "keywords":    list(keywords)[:80],
    }


def get_subject_default_topics(subject: str) -> Dict:
    """Return the built-in topic list for a subject (no upload needed)."""
    if subject not in SUBJECT_TOPICS:
        return {"units": [], "topics_flat": [], "keywords": []}
    units = []
    topics_flat = []
    keywords = set()
    for unit_name, unit_topics in SUBJECT_TOPICS[subject].items():
        units.append({"unit_name": unit_name, "topics": unit_topics})
        topics_flat.extend(unit_topics)
        for t in unit_topics:
            for w in t.split():
                if len(w) > 3:
                    keywords.add(w.lower())
    return {
        "units":       units,
        "topics_flat": list(dict.fromkeys(topics_flat)),
        "keywords":    list(keywords)[:80],
    }


def analyze_syllabus(raw_text: str, subject: str) -> Dict:
    """
    Full syllabus analysis pipeline.
    Returns structured data ready to store in the Syllabus model.
    """
    if not raw_text.strip():
        return get_subject_default_topics(subject)
    return extract_units_and_topics(raw_text, subject)
