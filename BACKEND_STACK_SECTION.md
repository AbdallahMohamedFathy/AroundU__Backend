# 4.2 Backend and Database Tools and Technologies

To support the high-concurrency, multi-tenant nature of the 7WALEEK platform, the core server-side architecture relies on a modern, asynchronous ecosystem. The backend stack is strategically chosen to ensure enterprise-grade data persistence, optimized geospatial query execution, robust object-relational mapping, and low-latency response times through distributed caching.

---

## 4.2.1 Core Web Server and Enterprise Framework

**FastAPI (Main Backend):** Utilized as the primary asynchronous web framework to build the core application logic and business rules. Operating on top of the Asynchronous Server Gateway Interface (ASGI) standard, it allows the server to process concurrent operations—such as simultaneous order placement and real-estate browsing—without blocking execution threads.

**Uvicorn:** Employed as the production-ready, lightning-fast ASGI server execution environment to host the main FastAPI application, bridging network requests to the asynchronous framework engine.

**Gunicorn:** Integrated as a battle-tested process manager in production deployments, operating in tandem with Uvicorn workers. Gunicorn manages worker lifecycle, graceful restarts, and process supervision, providing a stable and fault-tolerant execution environment for the ASGI application under sustained load.

**Pydantic:** Integrated deep within the request-response lifecycle to perform zero-cost data parsing and runtime constraint checking, ensuring that data injected by Flutter clients strictly complies with backend specifications before database commits.

**SlowAPI:** Deployed as a rate-limiting middleware layer built on top of the WSGI/ASGI stack. It enforces configurable per-endpoint request throttling thresholds—distinguishing between anonymous and authenticated users—to protect backend resources from abusive traffic patterns and denial-of-service attempts.

---

## 4.2.2 Database Management and Geospatial Extenders

**PostgreSQL:** Selected as the primary enterprise-grade Object-Relational Database Management System (ORDBMS). It guarantees absolute compliance with $ACID$ (Atomicity, Consistency, Isolation, Durability) properties, which are critical for processing secure e-commerce shopping carts, financial order entries, and persistent multi-tenant profiles.

**PostGIS Extension:** A spatial database extender deployed natively on top of PostgreSQL. It introduces specialized geographic data types (such as Geometry and Geography coordinates), spatial indexing options (like GiST indexes), and optimized spatial functions (such as $ST\_DWithin$ and $ST\_Distance$). This enables the backend to execute high-performance proximity searches and real-time location-based discoveries for users.

**GeoAlchemy2:** Deployed as the Python integration layer that bridges SQLAlchemy's ORM interface with the PostGIS spatial extension. It exposes PostGIS-native column types (such as `Geography(POINT, 4326)`) directly as SQLAlchemy column definitions, enabling the construction of geospatial queries—including distance-based filtering and spatial indexing—through Python objects rather than raw SQL strings.

**psycopg v3:** Utilized as the modern, low-level PostgreSQL database adapter for Python. It establishes and manages the direct binary communication channel between the SQLAlchemy engine and the PostgreSQL server, supporting both synchronous and asynchronous connection modes to accommodate the platform's hybrid execution model.

---

## 4.2.3 Object-Relational Mapping (ORM) and Schema Migrations

**SQLAlchemy:** Deployed as the industry-standard SQL Toolkit and Object-Relational Mapper (ORM). It abstracts complex database relational mappings into clean Python classes, preventing raw SQL string injections and ensuring optimal connection pooling parameters to handle high-frequency database operations. The platform employs a hybrid engine configuration: a synchronous engine (via `create_engine`) for the core application request cycle, and an asynchronous engine (via `create_async_engine`) for the order management subsystem, each tuned with dedicated connection pool parameters including pool size, overflow capacity, timeout, and periodic connection recycling intervals.

**Alembic:** Utilized as the database migration environment working in tandem with SQLAlchemy. It systematically tracks schema modifications, generates incremental transformation scripts, and executes production database upgrades/downgrades seamlessly without data loss or manual table reconstruction.

---

## 4.2.4 In-Memory Caching and Session Optimization

**Redis:** An open-source, in-memory key-value data structure store implemented as a distributed cache layer. It sits directly between the FastAPI application server and the PostgreSQL database to cache high-frequency, read-intensive data (such as active home-feed recommendations, user session states, and active token configurations), reducing database input/output bottlenecking and drastically optimizing tail-latencies.

**hiredis:** Integrated as a high-performance C-language parser accelerator for the Redis client. It replaces the default pure-Python response parser with a compiled binary module, significantly reducing CPU overhead during high-throughput Redis read operations and improving overall cache response throughput under peak concurrency conditions.
