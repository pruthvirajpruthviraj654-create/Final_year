# ============================================================
# services/ai_service.py — Advanced AI Question Generation Engine
# Supports: OpenRouter API + built-in syllabus-based fallback
# ============================================================
import requests
import json
import re
import random
from typing import List, Dict, Optional

from services.prompt_engine     import (build_mcq_prompt, build_short_prompt,
                                         build_medium_prompt, build_descriptive_prompt,
                                         build_long_prompt, build_full_paper_prompt,
                                         SYSTEM_PROMPT)
from services.syllabus_engine   import SUBJECT_TOPICS, get_subject_default_topics
from services.difficulty_engine import get_difficulty_config, get_marks_config, compute_section_distribution
from services.duplicate_checker import deduplicate_generated, check_syllabus_relevance

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# ── OpenRouter call ────────────────────────────────────────────
def _call_ai(prompt: str, api_key: str, model: str,
             max_tokens: int = 4000, temperature: float = 0.65) -> Optional[str]:
    if not api_key or len(api_key.strip()) < 15:
        return None
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {api_key.strip()}",
                "HTTP-Referer":  "https://examai.edu",
                "X-Title":       "ExamAI Smart Question Generator",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                "max_tokens":  max_tokens,
                "temperature": temperature,
                "top_p":       0.92,
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return content.strip()
    except Exception as exc:
        print(f"[AI] OpenRouter error: {exc}")
        return None


# ── Section parser ─────────────────────────────────────────────
def _parse_sections(text: str) -> Dict:
    sections = {}
    for letter in ["A", "B", "C", "D", "E"]:
        pattern = rf"SECTION\s+{letter}.*?(?=SECTION\s+[A-Z]|\*\*\*|END\s+OF|\Z)"
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            sections[letter] = m.group(0).strip()
    return sections


# ── Master generation entry point ──────────────────────────────
def generate_questions_ai(
    subject:      str,
    exam_type:    str,
    difficulty:   str,
    q_count:      int,
    total_marks:  int,
    duration:     str,
    bloom_level:  str,
    units:        List[str],
    q_types:      List[str],
    marks_config: List[Dict],   # [{type, marks_per_q, count}]
    topics:       List[str],    # from syllabus
    syllabus_context: str,      # raw syllabus text (first 1500 chars)
    api_key:      str,
    model:        str,
    college_name: str,
    department:   str,
) -> Dict:
    """
    Master function: generates a complete question paper.
    Returns {content, sections, metadata}
    """
    # Compute sections if not provided
    if not marks_config:
        marks_config = compute_section_distribution(total_marks, q_types)

    # Resolve topics: use syllabus topics or subject defaults
    if not topics:
        defaults = get_subject_default_topics(subject)
        topics = defaults.get("topics_flat", [])[:20]

    units_str = ", ".join(units) if units else "All Units"

    # Build full paper config
    config = dict(
        subject=subject, topics=topics, units_str=units_str,
        sections=marks_config, difficulty=difficulty, bloom_level=bloom_level,
        college_name=college_name, department=department,
        syllabus_context=syllabus_context[:1200], exam_type=exam_type,
        total_marks=total_marks, duration=duration,
    )

    prompt   = build_full_paper_prompt(config)
    raw_text = _call_ai(prompt, api_key, model)

    if not raw_text:
        raw_text = _fallback_generate(
            subject=subject, exam_type=exam_type, difficulty=difficulty,
            marks_config=marks_config, topics=topics,
            college_name=college_name, department=department,
            duration=duration, total_marks=total_marks,
            bloom_level=bloom_level, units_str=units_str,
        )

    sections = _parse_sections(raw_text)
    return {
        "content":        raw_text,
        "sections":       sections,
        "subject":        subject,
        "exam_type":      exam_type,
        "difficulty":     difficulty,
        "total_marks":    total_marks,
        "duration":       duration,
        "q_count":        q_count,
        "topics_used":    topics[:10],
        "syllabus_based": bool(syllabus_context.strip()),
        "ai_used":        bool(api_key and len(api_key.strip()) > 15),
    }


# ════════════════════════════════════════════════════════════════
# FALLBACK BUILT-IN GENERATOR
# Uses the rich SUBJECT_TOPICS knowledge base to produce
# properly formatted, syllabus-accurate papers without API.
# ════════════════════════════════════════════════════════════════

# ── Built-in question banks per subject ───────────────────────
QUESTION_BANK: Dict[str, Dict[str, List]] = {

    # ── DBMS ─────────────────────────────────────────────────
    "DBMS": {
        "MCQ": [
            ("Which of the following is NOT a feature of DBMS?",
             ["Data redundancy control","Data inconsistency","Data sharing","Data independence"], "B",
             "Database Management Systems"),
            ("The normalization form that removes partial dependencies is:",
             ["1NF","2NF","3NF","BCNF"], "B", "Normalization"),
            ("Which SQL clause is used to filter groups?",
             ["WHERE","HAVING","GROUP BY","ORDER BY"], "B", "SQL"),
            ("A foreign key in a relation refers to the ___ of another relation.",
             ["Primary key","Candidate key","Super key","Composite key"], "A", "Relational Model"),
            ("Which join returns all rows from both tables regardless of match?",
             ["INNER JOIN","LEFT JOIN","RIGHT JOIN","FULL OUTER JOIN"], "D", "SQL Joins"),
            ("ACID stands for:",
             ["Atomicity Consistency Isolation Durability","Accuracy Consistency Integrity Data",
              "Atomicity Correctness Isolation Distribution","None of the above"], "A", "Transactions"),
            ("Two-Phase Locking ensures:",
             ["Deadlock prevention","Serializability","Both A and B","Neither A nor B"], "B",
             "Concurrency Control"),
            ("B+ tree index differs from B-tree index in that:",
             ["B+ tree stores data only in leaves","B+ tree is slower","B-tree is balanced","B+ tree has fewer nodes"],
             "A", "Indexing"),
            ("Which of the following is a DDL command?",
             ["INSERT","UPDATE","CREATE","SELECT"], "C", "SQL Commands"),
            ("Relational algebra operation that removes duplicate tuples is:",
             ["Selection","Projection","Join","Division"], "B", "Relational Algebra"),
        ],
        "Short": [
            ("Define normalization. Why is it important in database design?", "Normalization", 2),
            ("What are ACID properties? Briefly explain each.", "Transactions", 2),
            ("Distinguish between DDL and DML with two examples each.", "SQL", 2),
            ("What is a foreign key? How does it enforce referential integrity?", "Relational Model", 2),
            ("Define ER model. List its main components.", "ER Model", 2),
            ("What is a deadlock in DBMS? How can it be detected?", "Concurrency Control", 2),
            ("Differentiate between primary key and candidate key.", "Keys", 2),
            ("What is a view in SQL? Write syntax to create a view.", "SQL Views", 2),
            ("Explain the concept of functional dependency with an example.", "Normalization", 2),
            ("What is an index in DBMS? State two advantages of indexing.", "Indexing", 2),
        ],
        "Medium": [
            ("Explain all types of JOINs in SQL with syntax and example tables showing output.", "SQL Joins", 5),
            ("Explain 1NF, 2NF, and 3NF with step-by-step conversion of an unnormalized relation to 3NF.", "Normalization", 5),
            ("Describe B+ tree indexing structure with insertion algorithm. Compare with B-tree.", "Indexing", 5),
            ("Explain Two-Phase Locking (2PL) protocol with a schedule example showing conflict serializability.", "Concurrency Control", 5),
            ("What is relational algebra? Explain: Select, Project, Join, Union, Difference with examples.", "Relational Algebra", 5),
            ("Write SQL queries for: (a) nested subqueries, (b) correlated subqueries, (c) set operations with examples.", "SQL Advanced", 5),
            ("Design an ER diagram for a 'Library Management System' showing all entities, attributes, and relationships.", "ER Diagram", 5),
            ("Explain BCNF with example. Compare BCNF with 3NF in terms of lossless join and dependency preservation.", "Normalization Advanced", 5),
        ],
        "Long": [
            (("Explain the three-tier client-server architecture of DBMS with a neat diagram. "
               "Discuss the role of each tier and advantages over file-based systems.", 5,
               "Describe log-based recovery with deferred and immediate database modification. "
               "Explain checkpoints and their role in reducing recovery time.", 5), "DBMS Architecture", 10),
            (("Design a complete ER diagram for a 'Hospital Management System' showing entities: "
               "Patient, Doctor, Ward, Medicine, Appointment with all attributes and relationships.", 5,
               "Convert the above ER diagram to relational tables. Apply normalization up to 3NF. "
               "Show all functional dependencies and decomposition steps.", 5), "Design Project", 10),
        ],
    },

    # ── Python ────────────────────────────────────────────────
    "Python": {
        "MCQ": [
            ("What is the output of: print(type(3//2))?",
             ["<class 'float'>","<class 'int'>","<class 'str'>","TypeError"], "B", "Data Types"),
            ("Which keyword is used to define a generator function?",
             ["generate","yield","return","async"], "B", "Generators"),
            ("Which of these is IMMUTABLE in Python?",
             ["list","dict","tuple","set"], "C", "Data Structures"),
            ("Correct syntax for lambda with two parameters:",
             ["lambda x y: x+y","lambda x,y: x+y","def lambda(x,y): x+y","func=x,y=>x+y"], "B", "Lambda"),
            ("What does __init__ do in a Python class?",
             ["Destroys the object","Initializes the object","Imports modules","Creates a function"], "B", "OOP"),
            ("Which method removes and returns the last element of a list?",
             ["remove()","del()","pop()","discard()"], "C", "List Operations"),
            ("Output of print(2**10):",
             ["20","1024","210","Error"], "B", "Operators"),
            ("Which exception is raised when dividing by zero?",
             ["ValueError","ZeroDivisionError","ArithmeticError","TypeError"], "B", "Exceptions"),
            ("What does the 'with' statement do in file handling?",
             ["Opens a file in write mode","Automatically closes file on exit","Creates a new file","None of above"], "B", "File Handling"),
            ("Which module provides regular expression support in Python?",
             ["regex","regexp","re","pattern"], "C", "Modules"),
        ],
        "Short": [
            ("Explain list comprehension in Python with three different examples.", "List Comprehension", 2),
            ("What are lambda functions? Compare with regular functions with examples.", "Lambda Functions", 2),
            ("Explain difference between deep copy and shallow copy with code example.", "Copy Operations", 2),
            ("Describe exception handling: try, except, else, finally with example.", "Exception Handling", 2),
            ("What are Python decorators? Write a simple timing decorator.", "Decorators", 2),
            ("Differentiate between *args and **kwargs with examples.", "Functions", 2),
            ("Explain the concept of inheritance in Python OOP with example.", "OOP Inheritance", 2),
            ("What is the difference between a list and a tuple in Python?", "Data Structures", 2),
            ("Explain file modes in Python: r, w, a, rb, wb with syntax.", "File Handling", 2),
            ("What is a Python module? How is it different from a package?", "Modules", 2),
        ],
        "Medium": [
            ("Design a Python class 'BankAccount' with attributes (account_no, owner, balance) and methods: deposit(), withdraw(), display_balance(). Show inheritance with 'SavingsAccount' that adds interest calculation.", "OOP Classes", 5),
            ("Implement a Stack data structure in Python using a list with: push(), pop(), peek(), isEmpty(), size(), display(). Include proper error handling for stack underflow.", "Data Structures", 5),
            ("Write a Python program using pandas to: (a) read a student marks CSV, (b) compute subject-wise averages, (c) find top 3 scorers, (d) save results to new CSV.", "Pandas", 5),
            ("Explain Python's OOP pillars: Encapsulation, Inheritance, Polymorphism, Abstraction each with a complete code example.", "OOP Concepts", 5),
            ("Implement Binary Search Tree in Python with: insert(), inorder(), search(), and delete() methods. Show output for inserting: 50, 30, 70, 20, 40, 60, 80.", "BST Implementation", 5),
        ],
        "Long": [
            (("Explain all OOP concepts in Python (Encapsulation, Inheritance, Polymorphism, Abstraction) "
               "using a real-world 'Vehicle Management System' scenario with complete code.", 5,
               "Build a REST API using Flask for a Student Management System with: GET all, GET by ID, "
               "POST (add student), PUT (update), DELETE. Use SQLite for storage.", 5), "OOP + Flask", 10),
        ],
    },

    # ── AI ────────────────────────────────────────────────────
    "AI": {
        "MCQ": [
            ("The Turing Test was designed to evaluate:",
             ["Robot speed","Machine intelligence","Network bandwidth","Database performance"], "B", "AI Introduction"),
            ("A* search uses heuristic function f(n) =",
             ["h(n)","g(n)","g(n) + h(n)","g(n) - h(n)"], "C", "Search Algorithms"),
            ("Which search algorithm is complete but not optimal?",
             ["BFS","DFS","A*","Greedy best-first"], "D", "Search Algorithms"),
            ("In a neural network, ReLU activation outputs:",
             ["max(0,x)","1/(1+e^-x)","tanh(x)","x^2"], "A", "Neural Networks"),
            ("Which learning type uses labeled training data?",
             ["Unsupervised","Reinforcement","Supervised","Semi-supervised"], "C", "Machine Learning"),
            ("Expert systems use which knowledge representation?",
             ["Semantic networks","Production rules (IF-THEN)","Frames","All of the above"], "D", "Knowledge Representation"),
            ("AO* algorithm is used for:",
             ["AND-OR graphs","Simple graphs","Directed graphs","Undirected graphs"], "A", "Search Algorithms"),
            ("Overfitting in ML means:",
             ["Model too simple","Model memorizes training data","Model is optimal","Data is too large"], "B", "Machine Learning"),
            ("Which is NOT a type of machine learning?",
             ["Supervised","Unsupervised","Programmed","Reinforcement"], "C", "ML Types"),
            ("In Bayesian networks, nodes represent:",
             ["Algorithms","Random variables","Edges","Probabilities"], "B", "Probability AI"),
        ],
        "Short": [
            ("Define AI. Distinguish between Weak AI, Strong AI, and General AI.", "AI Introduction", 2),
            ("Explain BFS and DFS with their time and space complexity.", "Search Algorithms", 2),
            ("What is a heuristic function? What makes a heuristic admissible?", "Heuristics", 2),
            ("State Bayes' theorem mathematically. Apply it to a spam detection example.", "Probability", 2),
            ("What is overfitting? How can it be prevented in machine learning?", "ML Concepts", 2),
            ("Define expert system. List its main components.", "Expert Systems", 2),
            ("What is reinforcement learning? Explain with an example.", "Reinforcement Learning", 2),
            ("Explain the difference between supervised and unsupervised learning.", "ML Types", 2),
        ],
        "Medium": [
            ("Explain A* search algorithm with a worked graph example. Show f(n)=g(n)+h(n) calculations. Compare with BFS and Greedy search.", "A* Algorithm", 5),
            ("Describe the architecture of a Multi-Layer Perceptron (MLP). Explain forward propagation with equations. Describe backpropagation.", "Neural Networks", 5),
            ("Explain k-means clustering step-by-step with pseudocode. Apply to dataset: {2,4,10,12,3,20,30,11,25} with k=3. Show all iterations.", "K-Means Clustering", 5),
            ("What are Decision Trees? Explain ID3 algorithm using entropy and information gain. Apply to a small weather dataset.", "Decision Trees", 5),
            ("Explain AO* algorithm with AND-OR graph example. Compare with A* algorithm.", "AO* Algorithm", 5),
        ],
        "Long": [
            (("Explain minimax algorithm with alpha-beta pruning. Apply to a 3-level game tree. "
               "Show how pruning reduces node evaluations with step-by-step trace.", 5,
               "Describe types of knowledge representation in AI: Semantic Networks, Frames, "
               "Predicate Logic, Production Rules. Compare with examples.", 5), "AI Core Topics", 10),
        ],
    },

    # ── CN ────────────────────────────────────────────────────
    "CN": {
        "MCQ": [
            ("Which OSI layer is responsible for routing packets?",
             ["Data Link","Network","Transport","Session"], "B", "OSI Model"),
            ("HTTPS uses port number:",
             ["80","21","443","25"], "C", "Application Layer"),
            ("IP address 192.168.1.1 belongs to class:",
             ["A","B","C","D"], "C", "IP Addressing"),
            ("TCP provides which type of service?",
             ["Connectionless unreliable","Connection-oriented reliable","Connectionless reliable","None"], "B", "Transport Layer"),
            ("DNS resolves:",
             ["IP to MAC address","Domain name to IP address","IP to port","None of above"], "B", "Application Layer"),
            ("Which protocol is used for email sending?",
             ["POP3","IMAP","SMTP","FTP"], "C", "Application Protocols"),
            ("Subnetting is used to:",
             ["Increase bandwidth","Divide a network into smaller networks","Connect two networks","None"], "B", "Subnetting"),
            ("CRC is used for:",
             ["Encryption","Error detection","Compression","Routing"], "B", "Error Control"),
            ("In OSI model, which layer handles encryption?",
             ["Physical","Data Link","Presentation","Session"], "C", "OSI Model"),
            ("ARP is used to find:",
             ["IP address from MAC","MAC address from IP","Port from IP","None"], "B", "Network Layer"),
        ],
        "Short": [
            ("Explain the OSI model with all 7 layers and their primary functions.", "OSI Model", 2),
            ("What is subnetting? Calculate subnets for 192.168.10.0/26.", "Subnetting", 2),
            ("Compare TCP and UDP with respect to: connection, reliability, speed, use cases.", "Transport Layer", 2),
            ("What is DNS? Explain the DNS resolution process step by step.", "DNS", 2),
            ("What is NAT? Explain static, dynamic, and PAT with examples.", "NAT", 2),
            ("Explain the difference between a hub, switch, and router.", "Network Devices", 2),
            ("What is CSMA/CD? Where is it used?", "Data Link Layer", 2),
            ("Differentiate between IPv4 and IPv6 with examples.", "IP Addressing", 2),
        ],
        "Medium": [
            ("Explain TCP three-way handshake and four-way termination with diagrams. What happens if a segment is lost?", "TCP", 5),
            ("Explain RSA encryption algorithm step by step. Use p=11, q=13 to demonstrate key generation, encrypt M=7, and decrypt.", "Network Security", 5),
            ("Describe CSMA/CD and CSMA/CA protocols. How do they handle collisions? Compare Ethernet vs Wi-Fi.", "MAC Protocols", 5),
            ("Compare Distance Vector and Link State routing algorithms. Explain RIP (Distance Vector) with convergence example.", "Routing", 5),
            ("Explain sliding window protocol. Compare Stop-and-Wait, Go-Back-N, and Selective Repeat with efficiency formula.", "Flow Control", 5),
        ],
        "Long": [
            (("Design a complete network for a university with 5 departments, 1000 nodes, central server room. "
               "Specify topology, IP addressing scheme, hardware requirements.", 5,
               "Explain SSL/TLS handshake process step by step. How does HTTPS secure communication? "
               "Explain certificates, CAs, and symmetric key exchange.", 5), "Network Design + Security", 10),
        ],
    },

    # ── OS ────────────────────────────────────────────────────
    "OS": {
        "MCQ": [
            ("Which scheduling algorithm gives minimum average waiting time for known burst times?",
             ["FCFS","Round Robin","SJF","Priority"], "C", "CPU Scheduling"),
            ("Thrashing in OS occurs due to:",
             ["High CPU utilization","Excessive page faults","Full disk","Slow I/O"], "B", "Virtual Memory"),
            ("Which is NOT a necessary condition for deadlock?",
             ["Mutual exclusion","Preemption","Hold and wait","Circular wait"], "B", "Deadlock"),
            ("LRU page replacement replaces:",
             ["Most recently used page","Least recently used page","First loaded page","Random page"], "B", "Page Replacement"),
            ("Banker's algorithm is used for:",
             ["Memory management","Deadlock avoidance","CPU scheduling","File systems"], "B", "Deadlock"),
            ("In Round Robin, if time quantum is very large, it behaves like:",
             ["SJF","Priority","FCFS","HRRN"], "C", "CPU Scheduling"),
            ("Which memory allocation strategy has no external fragmentation?",
             ["First fit","Best fit","Worst fit","Paging"], "D", "Memory Management"),
            ("Fork() system call creates:",
             ["Thread","Child process","Zombie process","Daemon"], "B", "Process Management"),
            ("Semaphore wait(P) operation:",
             ["Increments semaphore","Decrements semaphore","Tests semaphore","Resets semaphore"], "B", "Synchronization"),
            ("Which page replacement has lowest page fault rate theoretically?",
             ["FIFO","LRU","Optimal","LFU"], "C", "Page Replacement"),
        ],
        "Short": [
            ("State Coffman's four necessary conditions for deadlock with one-line explanation for each.", "Deadlock", 2),
            ("Explain virtual memory and demand paging. When is a page fault generated?", "Virtual Memory", 2),
            ("Differentiate between process and thread. List advantages of multithreading.", "Process Management", 2),
            ("What is a semaphore? Distinguish between binary semaphore and counting semaphore.", "Synchronization", 2),
            ("Explain context switching. What information is saved in PCB?", "Process Management", 2),
            ("Compare preemptive and non-preemptive scheduling with examples.", "CPU Scheduling", 2),
            ("What is internal and external fragmentation? How does paging solve fragmentation?", "Memory Management", 2),
            ("Explain the concept of critical section problem and its three requirements.", "Synchronization", 2),
        ],
        "Medium": [
            ("Apply FCFS, SJF (non-preemptive), and Round Robin (TQ=2ms) for: P1=6ms, P2=8ms, P3=4ms, P4=3ms. Draw Gantt charts. Calculate average waiting time for each.", "CPU Scheduling", 5),
            ("Explain Banker's Algorithm for deadlock avoidance. Apply to: 5 processes, 3 resources (A=10,B=5,C=7). Show safety sequence.", "Deadlock Avoidance", 5),
            ("Compare FIFO, LRU, and Optimal page replacement. Apply to reference string: 7,0,1,2,0,3,0,4,2,3,0,3 with 3 frames.", "Page Replacement", 5),
            ("Explain Producer-Consumer problem. Provide complete solution using semaphores with pseudocode. Verify correctness.", "Synchronization", 5),
            ("Describe disk scheduling algorithms: FCFS, SSTF, SCAN, C-SCAN. Apply to requests: 98,183,37,122,14,124,65,67 with head at 53.", "Disk Scheduling", 5),
        ],
        "Long": [
            (("Explain Unix file system structure: boot block, superblock, inode table, data blocks. "
               "Describe how a file is located using inodes and directory entries with example.", 5,
               "Explain Dining Philosophers problem. Present semaphore solution and identify deadlock potential. "
               "Provide a deadlock-free solution using resource ordering or monitor.", 5), "OS Concepts", 10),
        ],
    },

    # ── Java ──────────────────────────────────────────────────
    "Java": {
        "MCQ": [
            ("JVM stands for:",
             ["Java Visual Mode","Java Virtual Machine","Java Variable Manager","Java Version Model"], "B", "Java Basics"),
            ("Which access modifier allows access from everywhere?",
             ["private","protected","public","default"], "C", "Access Modifiers"),
            ("Java is both compiled and interpreted because:",
             ["It uses C compiler","Bytecode runs on JVM","Both A and B","None"], "B", "JVM"),
            ("Which keyword prevents a class from being subclassed?",
             ["static","abstract","final","private"], "C", "OOP Concepts"),
            ("Which collection does NOT allow duplicate values?",
             ["ArrayList","LinkedList","HashSet","Vector"], "C", "Collections"),
            ("Checked exceptions must be:",
             ["Only caught","Only declared","Caught or declared","Ignored"], "C", "Exception Handling"),
            ("'super' keyword is used to:",
             ["Create object","Reference parent class","Define interface","Override"], "B", "Inheritance"),
            ("Which interface must be implemented for multithreading?",
             ["Serializable","Comparable","Runnable","Cloneable"], "C", "Multithreading"),
            ("What is the output of: System.out.println(10/3)?",
             ["3.33","3","3.0","Error"], "B", "Operators"),
            ("Which Java keyword enables runtime polymorphism?",
             ["overload","override","extend","implement"], "B", "Polymorphism"),
        ],
        "Short": [
            ("Explain compile-time and runtime polymorphism in Java with code examples.", "Polymorphism", 2),
            ("What is a Java interface? How is it different from an abstract class?", "Interfaces", 2),
            ("Explain Java Memory Model: Stack vs Heap. What is garbage collection?", "Memory Management", 2),
            ("Differentiate checked and unchecked exceptions. Give two examples of each.", "Exception Handling", 2),
            ("What is the Java Collections Framework? Name 4 important collection classes.", "Collections", 2),
            ("What is method overloading? How does it differ from method overriding?", "Polymorphism", 2),
            ("Explain the 'this' and 'super' keywords in Java with examples.", "OOP Basics", 2),
            ("What is synchronization in Java? When is it needed?", "Multithreading", 2),
        ],
        "Medium": [
            ("Implement a Singly Linked List in Java with: insertAtHead(), insertAtTail(), deleteByValue(), search(), reverse(), display().", "Data Structures in Java", 5),
            ("Create Java interface 'Shape' with abstract methods area() and perimeter(). Implement with Circle, Rectangle, Triangle. Demonstrate runtime polymorphism.", "OOP Design", 5),
            ("Implement Producer-Consumer problem in Java using threads. Use synchronized, wait(), notify() with a shared buffer of size 5.", "Multithreading", 5),
            ("Write a Java program for Binary Search Tree with: insert(), inorderTraversal(), search(), delete() covering all three deletion cases.", "BST in Java", 5),
            ("Explain Java Generics. Implement a generic Stack<T> class. Explain bounded type parameters (extends, super) with examples.", "Generics", 5),
        ],
        "Long": [
            (("Explain Java exception handling. Create custom exceptions for a Banking System: "
               "InsufficientFundsException, AccountNotFoundException. Demonstrate try-catch-finally and throws.", 5,
               "Design a multithreaded banking simulation in Java. Multiple threads perform simultaneous "
               "deposits/withdrawals. Use synchronization to prevent race conditions.", 5), "Java Advanced", 10),
        ],
    },

    # ── DS ────────────────────────────────────────────────────
    "DS": {
        "MCQ": [
            ("Time complexity of Binary Search:",
             ["O(n)","O(n²)","O(log n)","O(1)"], "C", "Searching"),
            ("Which data structure uses LIFO principle?",
             ["Queue","Stack","Tree","Graph"], "B", "Stacks"),
            ("Which sorting algorithm has best average-case time complexity?",
             ["Bubble Sort","Insertion Sort","Merge Sort","Selection Sort"], "C", "Sorting"),
            ("AVL tree is a:",
             ["Binary tree","Complete binary tree","Height-balanced BST","Min-heap"], "C", "Trees"),
            ("Dijkstra's algorithm is used to find:",
             ["Minimum spanning tree","Shortest path","Maximum flow","Topological sort"], "B", "Graphs"),
            ("In a queue, insertion happens at:",
             ["Front","Rear","Both ends","Middle"], "B", "Queues"),
            ("Inorder traversal of a BST gives:",
             ["Random sequence","Sorted ascending sequence","Sorted descending sequence","Level order"], "B", "BST"),
            ("Hash collision resolved by chaining uses:",
             ["Array","Linked list","Stack","Queue"], "B", "Hashing"),
            ("Which traversal visits root LAST?",
             ["Preorder","Inorder","Postorder","Level order"], "C", "Tree Traversal"),
            ("Time complexity of Merge Sort:",
             ["O(n)","O(n log n)","O(n²)","O(log n)"], "B", "Sorting"),
        ],
        "Short": [
            ("Define algorithm. State its five key characteristics.", "Algorithm Analysis", 2),
            ("Explain recursion with factorial example. State advantages and disadvantages.", "Recursion", 2),
            ("Compare array and linked list with respect to memory, access, insertion, deletion.", "Linear Structures", 2),
            ("What is BST property? Write the search algorithm with time complexity.", "BST", 2),
            ("Explain Big-O, Omega, and Theta notation with examples.", "Complexity Analysis", 2),
            ("What is AVL tree? State the AVL property and types of rotations.", "AVL Trees", 2),
            ("Explain BFS and DFS traversals. Which uses queue and which uses stack?", "Graph Traversal", 2),
            ("What is hashing? Explain separate chaining for collision resolution.", "Hashing", 2),
        ],
        "Medium": [
            ("Explain Merge Sort with pseudocode and trace on: [38,27,43,3,9,82,10]. Analyze time and space complexity.", "Merge Sort", 5),
            ("Implement AVL tree insertions. Insert: 10,20,30,40,50,25. Show all rotations (LL,RR,LR,RL) with diagrams.", "AVL Trees", 5),
            ("Explain Dynamic Programming with principle of optimal substructure. Solve 0/1 Knapsack: weights=[2,3,4,5], values=[3,4,5,7], capacity=5.", "Dynamic Programming", 5),
            ("Explain Dijkstra's shortest path algorithm. Apply on a weighted graph with 6 vertices. Show step-by-step distance table.", "Graph Algorithms", 5),
            ("Compare graph representations: adjacency matrix vs adjacency list. Implement BFS and DFS on the same graph.", "Graphs", 5),
        ],
        "Long": [
            (("Explain heap data structure. Implement max-heap with heapify, insert, extract-max. "
               "Apply heap sort on: [4,10,3,5,1]. Analyze time complexity.", 5,
               "Explain Prim's and Kruskal's MST algorithms. Apply both on the same weighted graph. "
               "Compare their time complexities and use cases.", 5), "Advanced Data Structures", 10),
        ],
    },

    # ── ML ────────────────────────────────────────────────────
    "ML": {
        "MCQ": [
            ("The bias-variance tradeoff in ML refers to:",
             ["Speed vs accuracy","Underfitting vs overfitting","Train vs test split","None"], "B", "ML Fundamentals"),
            ("Which algorithm uses information gain for splitting?",
             ["KNN","Decision Tree","SVM","Naive Bayes"], "B", "Decision Trees"),
            ("Cross-validation is used to:",
             ["Speed up training","Estimate model performance","Reduce dimensions","Normalize data"], "B", "Model Evaluation"),
            ("In K-means, K represents:",
             ["Iterations","Clusters","Features","Neighbors"], "B", "Clustering"),
            ("Support Vector Machine finds:",
             ["Decision boundary","Hyperplane with maximum margin","Optimal k","None"], "B", "SVM"),
            ("Which activation function can cause vanishing gradient problem?",
             ["ReLU","Sigmoid","Leaky ReLU","Linear"], "B", "Neural Networks"),
            ("Regularization in ML is used to:",
             ["Speed up training","Prevent overfitting","Increase model complexity","None"], "B", "Regularization"),
            ("Random Forest is an example of:",
             ["Single model","Ensemble method","Clustering","Dimensionality reduction"], "B", "Ensemble Methods"),
        ],
        "Short": [
            ("Define supervised learning. Give three real-world examples.", "ML Basics", 2),
            ("What is the confusion matrix? Define precision, recall, and F1-score.", "Model Evaluation", 2),
            ("Explain gradient descent. What is the role of learning rate?", "Optimization", 2),
            ("What is regularization? Distinguish between L1 (Lasso) and L2 (Ridge).", "Regularization", 2),
            ("Define K-nearest neighbor algorithm. How is K selected?", "KNN", 2),
        ],
        "Medium": [
            ("Explain logistic regression for binary classification. Derive the sigmoid function and decision boundary.", "Logistic Regression", 5),
            ("Describe Random Forest algorithm. Explain bagging, feature sampling, and how final prediction is made.", "Ensemble Methods", 5),
            ("Explain Naive Bayes classifier. Apply Bayes theorem to email spam classification example.", "Naive Bayes", 5),
            ("Explain Principal Component Analysis (PCA) step by step. When is dimensionality reduction needed?", "Dimensionality Reduction", 5),
        ],
        "Long": [
            (("Explain the architecture of a Convolutional Neural Network (CNN). "
               "Describe convolution, pooling, and fully connected layers with equations.", 5,
               "Explain backpropagation algorithm in neural networks with chain rule derivation. "
               "Apply to a 2-layer network example with forward and backward pass.", 5), "Deep Learning", 10),
        ],
    },

    # ── SE ────────────────────────────────────────────────────
    "SE": {
        "MCQ": [
            ("Which SDLC model is best for projects with well-defined requirements?",
             ["Agile","Spiral","Waterfall","RAD"], "C", "SDLC Models"),
            ("Cohesion measures:",
             ["Dependency between modules","Relatedness within a module","Code size","Bug count"], "B", "Design Principles"),
            ("SRS document stands for:",
             ["Software Requirements Specification","System Requirements Study","Software Release Specification","None"], "A", "Requirements Engineering"),
            ("Black-box testing focuses on:",
             ["Code structure","Internal logic","Input-output behavior","Algorithms"], "C", "Software Testing"),
            ("COCOMO model is used for:",
             ["Testing","Cost estimation","Design","Deployment"], "B", "Project Management"),
            ("Agile methodology emphasizes:",
             ["Comprehensive documentation","Working software over documentation","Fixed requirements","Long planning phase"], "B", "Agile"),
            ("Cyclomatic complexity measures:",
             ["Code size","Number of linearly independent paths","Bug density","Performance"], "B", "Testing Metrics"),
            ("Coupling refers to:",
             ["Internal module strength","Degree of interdependence between modules","Code length","Test coverage"], "B", "Design Principles"),
        ],
        "Short": [
            ("Compare Waterfall and Agile models. When is each appropriate?", "SDLC Models", 2),
            ("What is cohesion? List types from lowest to highest cohesion.", "Software Design", 2),
            ("Define functional and non-functional requirements with two examples each.", "Requirements Engineering", 2),
            ("What is software testing? Distinguish between verification and validation.", "Software Testing", 2),
            ("Explain risk management in software projects. List four types of risks.", "Project Management", 2),
        ],
        "Medium": [
            ("Explain Scrum framework with all roles, artifacts, and ceremonies. How does it differ from traditional project management?", "Agile/Scrum", 5),
            ("Describe software design principles: Modularity, Abstraction, Information Hiding, Stepwise Refinement. Give examples.", "Design Principles", 5),
            ("Explain white-box and black-box testing. Design test cases using equivalence partitioning and boundary value analysis for function: int divide(int a, int b).", "Software Testing", 5),
        ],
        "Long": [
            (("Draw and explain all types of UML diagrams with examples: Use Case, Class, Sequence, "
               "Activity, and State diagrams for a 'Library Management System'.", 5,
               "Explain software configuration management. Describe Git workflow: branching strategies, "
               "merging, conflict resolution, and CI/CD pipeline integration.", 5), "SE Tools & Practices", 10),
        ],
    },
}


def _fallback_generate(
    subject: str, exam_type: str, difficulty: str,
    marks_config: List[Dict], topics: List[str],
    college_name: str, department: str,
    duration: str, total_marks: int,
    bloom_level: str, units_str: str,
) -> str:
    """Generate paper from built-in question bank (no API required)."""
    bank = QUESTION_BANK.get(subject, QUESTION_BANK.get("DS", {}))
    lines = []

    # ── Header ────────────────────────────────────────────────
    lines += [
        college_name.upper(),
        f"Department of {department}",
        f"{exam_type} — April 2025",
        "",
        f"Subject: {subject}" + " " * 20 + "Subject Code: CS-XXX",
        f"Duration: {duration}" + " " * 16 + f"Maximum Marks: {total_marks}",
        f"Units: {units_str}" + " " * 10 + f"Bloom's Level: {bloom_level}",
        "",
        "━" * 68,
        "",
        "INSTRUCTIONS TO CANDIDATES:",
        "1. All questions are compulsory unless stated otherwise.",
        "2. Figures to the right indicate full marks for each question.",
        "3. Assume suitable data wherever necessary and state assumptions clearly.",
        "4. Use of mobile phones or programmable calculators is strictly prohibited.",
        "5. Write your Enrollment Number and Full Name on the answer book.",
        "",
        "━" * 68,
    ]

    q_num     = 1
    type_map  = {"MCQ": "MCQ", "Short": "Short", "Medium": "Medium",
                 "Descriptive": "Descriptive", "Long": "Long"}
    sec_labels = ["A", "B", "C", "D", "E"]

    for sec_idx, sec in enumerate(marks_config):
        sec_letter  = sec_labels[sec_idx] if sec_idx < len(sec_labels) else chr(65 + sec_idx)
        q_type      = sec.get("type", "Short")
        marks_per_q = sec.get("marks_per_q", 2)
        count       = sec.get("count", 3)
        sec_marks   = sec.get("section_marks", count * marks_per_q)

        # Section header
        type_name = {
            "MCQ": "Multiple Choice Questions",
            "Short": "Short Answer Questions",
            "Medium": "Medium Answer Questions",
            "Descriptive": "Descriptive Questions",
            "Long": "Long Answer Questions",
        }.get(q_type, "Questions")

        lines += [
            "",
            f"SECTION {sec_letter} — {type_name.upper()}" + " " * 8 + f"[{sec_marks} Marks]",
            f"(Each question carries {marks_per_q} mark{'s' if marks_per_q > 1 else ''}. "
            + ("Attempt ALL." if q_type in ["MCQ","Short"] else f"Attempt any {max(1,count-1)} out of {count}."),
            "",
        ]

        # Get questions from bank
        bank_qs = bank.get(q_type if q_type in bank else
                           ("Long" if marks_per_q >= 8 else
                            "Medium" if marks_per_q >= 4 else
                            "Short" if marks_per_q == 2 else "MCQ"), [])
        bank_qs = list(bank_qs)
        random.shuffle(bank_qs)
        selected = bank_qs[:count]

        for q in selected:
            if q_type == "MCQ" and len(q) >= 3:
                qtext, opts, correct, topic = q[0], q[1], q[2], (q[3] if len(q) > 3 else "")
                lines.append(f"Q{q_num}. {qtext}")
                for letter, opt in zip(["a","b","c","d"], opts):
                    lines.append(f"    {letter}) {opt}")
                lines.append(f"    ✓ Correct Answer: {correct}) {opts['ABCD'.index(correct)] if correct in 'ABCD' and 'ABCD'.index(correct) < len(opts) else ''}")
                lines.append(f"    [Topic: {topic}]   [Marks: 1]")
                lines.append("")

            elif q_type == "Long" and isinstance(q[0], tuple):
                part = q[0]
                lines.append(f"Q{q_num}.")
                lines.append(f"    (a) {part[0]}" + " " * max(1, 50-len(part[0])) + f"[{part[1]} Marks]")
                lines.append("")
                lines.append(f"    (b) {part[2]}" + " " * max(1, 50-len(part[2])) + f"[{part[3]} Marks]")
                lines.append("")

            else:
                # Short / Medium / Descriptive
                if isinstance(q, tuple):
                    qtext = q[0]
                    topic = q[1] if len(q) > 1 else ""
                    marks = q[2] if len(q) > 2 else marks_per_q
                else:
                    qtext = str(q)
                    topic = ""
                    marks = marks_per_q
                lines.append(f"Q{q_num}. {qtext}" + " " * max(1, 55-len(qtext[:50])) + f"[{marks} Marks]")
                if topic:
                    lines.append(f"    [Topic: {topic}]")
                lines.append("")

            q_num += 1

        lines += ["━" * 68, ""]

    lines += [
        "",
        " " * 22 + "*** END OF QUESTION PAPER ***",
        " " * 10 + f"Generated by ExamAI Platform  |  Syllabus-Based Generation  |  {subject}",
    ]
    return "\n".join(lines)
