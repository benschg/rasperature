# Cloud IoT Platform Cost & Infrastructure Analysis

**Scale Requirements:**
- 100 customers
- 1,000 sensors per customer = 100,000 total sensors
- 2 values per second per sensor
- ~100 bytes per message (JSON format)

## Data Volume Calculations

```
Messages per second:  200,000 msg/sec
Messages per minute:  12,000,000 msg/min
Messages per hour:    720,000,000 msg/hour
Messages per day:     17,280,000,000 msg/day (17.28 billion)
Messages per month:   518,400,000,000 msg/month (518.4 billion)

Data per second:      20 MB/sec
Data per day:         1.728 TB/day
Data per month:       51.84 TB/month

Bandwidth required:   160 Mbps sustained (400 Mbps peak capacity needed)
```

---

## Cost Comparison Summary

| Rank | Platform | Monthly Cost | Per Customer | Per Sensor | Viable? | Complexity |
|------|----------|--------------|--------------|------------|---------|------------|
| 1 | **Google Cloud** (Pub/Sub + BigQuery) | **$7,505** | $75.05 | $0.08 | ✅ Yes | Medium |
| 2 | **Self-Hosted** (Bare Metal + Staff) | **$17,432** | $174.32 | $0.17 | ✅ Yes | High |
| 3 | **Kafka + Clickhouse** (Self-hosted) | **$16,532** | $165.32 | $0.17 | ✅ Yes | High |
| 4 | **Azure IoT** (Optimized) | **$38,948** | $389.48 | $0.39 | ✅ Yes | Medium |
| 5 | **InfluxDB Dedicated** (Negotiated) | **$50K-150K** | $500-1,500 | $0.50-1.50 | ✅ Yes | Low |
| 6 | **Azure IoT Hub** + ADX | **$162,593** | $1,625.93 | $1.63 | ✅ Yes | Low |
| 7 | **InfluxDB Cloud** (Usage-based) | **$1,051,227** | $10,512.27 | $10.51 | ❌ Too expensive | Low |
| 8 | **AWS IoT + DynamoDB** | **$1,257,868** | $12,578.68 | $12.58 | ❌ Too expensive | Low |
| 9 | **AWS IoT + Timestream** | **$2,210,527** | $22,105.27 | $22.11 | ❌ Too expensive | Low |
| 10 | **ThingSpeak** | **$833,333** | $8,333.33 | $8.33 | ❌ Not viable | N/A |

---

## Top 3 Detailed Recommendations

### 1. Google Cloud (Pub/Sub + BigQuery) - WINNER for Cost

**Monthly Cost: $7,505** ($0.08/sensor/month)

**Cost Breakdown:**
```
Pub/Sub Ingestion:           $1,446
BigQuery Active Storage:     $1,037
BigQuery Long-term Storage:  $1,037
BigQuery Queries (est):      $3,500
Data Transfer Out:           $462
GCS Staging:                 $24
────────────────────────────────────
TOTAL:                       $7,505
```

**Architecture:**
```
Raspberry Pi → MQTT Bridge (Cloud Run) → Pub/Sub → BigQuery
                                            ↓
                                    Bigtable (real-time queries)
                                            ↓
                                    Custom UI (REST API)
```

**Pros:**
- ✅ Lowest cloud cost (294x cheaper than AWS IoT Core)
- ✅ Excellent for analytics with BigQuery SQL
- ✅ Fully managed, auto-scaling
- ✅ Global distribution
- ✅ 99.95% SLA on Pub/Sub
- ✅ Great REST API for custom UI development

**Cons:**
- ❌ No native MQTT (requires custom bridge via Cloud Run)
- ❌ Requires more development work
- ❌ BigQuery not optimized for real-time queries (use Bigtable for real-time)

**Stability:**
- Pub/Sub handles 100K+ msg/sec per topic
- No connection limits (stateless)
- Auto-scales horizontally
- Can handle 10x your current load

**When to Choose:**
- Cost is primary concern
- You have development resources for custom MQTT bridge
- Analytics/historical data more important than real-time
- Building custom UI (excellent APIs)

---

### 2. Azure IoT Hub + Azure Data Explorer (Optimized) - BEST Managed Solution

**Monthly Cost: $38,948** ($0.39/sensor/month) with edge downsampling

**Cost Breakdown (Optimized):**
```
IoT Hub (12 units × $2,500):    $30,000
Azure Data Explorer (4 inst):   $7,948
Hot Storage:                    $800
Data Transfer:                  $200
────────────────────────────────────
TOTAL:                          $38,948
```

**Cost Breakdown (Unoptimized):**
```
IoT Hub (58 units × $2,500):    $145,000
Azure Data Explorer (8 inst):   $15,898
Hot Storage:                    $1,037
Cold Storage:                   $207
Data Transfer:                  $451
────────────────────────────────────
TOTAL:                          $162,593
```

**Optimization Strategy:**
1. **Edge Downsampling:** Only send data when values change >0.5°C or >2 hPa (reduces 60-80%)
2. **Local Aggregation:** Send 1-minute averages instead of raw 2 readings/sec
3. **Result:** 518.4B messages → 100-130B messages (75% reduction)

**Architecture:**
```
Raspberry Pi (with edge logic) → Azure IoT Hub → Azure Data Explorer
                                                        ↓
                                                  Custom UI (REST/WebSocket)
```

**Pros:**
- ✅ Fully managed IoT platform
- ✅ Native MQTT support (no bridge needed)
- ✅ Excellent time-series database (Azure Data Explorer)
- ✅ 99.9% SLA
- ✅ Good balance of ease and cost
- ✅ Device management features (shadows, twins)
- ✅ Real-time and historical queries

**Cons:**
- ❌ Requires edge optimization for best pricing
- ❌ Manual scaling (not automatic)
- ❌ Still moderately expensive

**Stability:**
- 6,000 msg/sec per IoT Hub unit
- 348,000 msg/sec total capacity (with 58 units)
- 72,000 msg/sec with optimization (12 units)
- Unlimited device identities on S3 tier

**When to Choose:**
- Want fully managed solution
- Need native MQTT support
- Time-series analytics important
- Limited DevOps resources
- Can implement edge optimization

---

### 3. Self-Hosted (Bare Metal) - BEST Long-term Economics

**Infrastructure Cost: $3,932/month**
**TCO (with DevOps): $17,432/month** ($0.17/sensor/month)

**Cost Breakdown:**
```
MQTT Brokers (5 × Hetzner AX101):      $815
Database Cluster (6 × Hetzner SX293):  $1,438
Additional Storage (100 TB):           $1,094
Load Balancer (HAProxy):               $50
Bandwidth:                             $35
Backup & Monitoring:                   $500
──────────────────────────────────────────────
Infrastructure Subtotal:               $3,932

DevOps Staff (1 FTE):                  $12,500
Security & DDoS Protection:            $1,000
──────────────────────────────────────────────
TOTAL TCO:                             $17,432
```

**Recommended Stack:**
```
Raspberry Pi → EMQX (MQTT Cluster) → Kafka → TimescaleDB/Clickhouse → Grafana
                                        ↓                                  ↓
                                   Redis (cache)                   Custom API/UI
```

**Alternative Stack:**
```
Raspberry Pi → Mosquitto Cluster → Telegraf → InfluxDB → Custom API/UI
```

**Pros:**
- ✅ Lowest per-sensor cost at scale
- ✅ Complete control and customization
- ✅ No vendor lock-in
- ✅ Best margins for growth beyond 100 customers
- ✅ Data sovereignty and privacy
- ✅ Can run in specific geographic regions

**Cons:**
- ❌ Requires 6+ months to build initially
- ❌ Need dedicated DevOps team (1-2 FTEs)
- ❌ You own reliability/uptime
- ❌ Higher operational complexity
- ❌ Security updates and patching responsibility

**Stability:**
- EMQX handles 1M+ concurrent connections
- Kafka proven at LinkedIn/Uber scale (millions msg/sec)
- TimescaleDB/Clickhouse handle TB/day ingestion
- 99.9%+ achievable with proper setup
- Requires multi-region setup for geographic redundancy

**Hidden Costs:**
- Initial development: 6-12 months × $150K/year salary = $75K-150K
- Ongoing maintenance: 1-2 FTEs × $150K/year = $150K-300K/year
- On-call support: $30K-50K/year
- Security certifications (SOC2, ISO 27001): $50K-150K/year

**When to Choose:**
- Long-term project (3+ years to recoup development costs)
- Have DevOps team in place
- Need lowest per-unit cost at scale
- Growing beyond 100 customers
- Data sovereignty requirements
- Want complete control over architecture

---

## Why AWS IoT Core Is So Expensive

**AWS IoT Core + Timestream: $2,210,527/month (294x more than Google Cloud)**

### Breakdown of AWS Costs:

```
AWS IoT Core Connectivity:        $346
AWS IoT Core Messaging:           $518,400
IoT Rules Engine:                 $77,760
Timestream Writes:                $259,200
Timestream Memory Storage:        $1,342,848  ← THIS IS THE KILLER
Timestream Magnetic Storage:      $3,110
Timestream Queries (est):         $7,500
Data Transfer:                    $1,363
──────────────────────────────────────────────
TOTAL:                            $2,210,527
```

### Detailed Explanation: The "AWS IoT Tax"

#### 1. Premium Managed IoT Service Pricing

AWS IoT Core is a **specialized, fully-managed IoT platform** with premium pricing:

**Messaging Cost Comparison:**
```
518.4 billion messages/month

AWS IoT Core:     $1.00/million = $518,400/month
Google Pub/Sub:   $0.003/million* = $1,446/month  (358x cheaper)
Self-hosted MQTT: $0.0016/million** = $815/month  (634x cheaper)

*Calculated: $1,446 total / 518,400 million messages = $0.003/million
**Infrastructure cost only, divided by message volume
```

**Why the difference?**
- AWS IoT Core = **"IoT as a Service"** (premium managed platform)
- Google Pub/Sub = **"Commodity message queue"** (general-purpose infrastructure)
- Self-hosted = **"Raw infrastructure"** (you manage everything)

#### 2. Timestream Memory Storage - The Major Cost Driver

Amazon Timestream's memory storage is the biggest cost factor:

```
Storage Cost Breakdown:

51.84 TB × $0.036/GB-hour × 720 hours/month = $1,342,848/month

Compare to alternatives:
- Timestream (memory):    $25.92/GB-month  = $1,342,848
- DynamoDB (SSD):         $0.25/GB-month   = $12,960      (104x cheaper)
- BigQuery (active):      $0.02/GB-month   = $1,037       (1,295x cheaper)
- PostgreSQL (self):      $0.125/GB-month  = $6,480       (207x cheaper)
- S3 Glacier (archive):   $0.004/GB-month  = $207         (6,495x cheaper)
```

**Why is Timestream so expensive?**
- Designed for **sub-millisecond query latency** on recent data
- Keeps data in **in-memory storage** for ultra-fast access
- Premium pricing for premium performance
- Optimized for real-time analytics, not bulk storage

**The problem:** At your scale (51.84 TB/month), memory storage costs alone exceed most competitors' **total** platform costs.

#### 3. Enterprise Feature Overhead

With AWS IoT Core, you're paying for comprehensive features:

**Included Features:**
- ✅ Device Registry - Manage 100K devices with metadata
- ✅ Device Shadows - Cached device state in cloud
- ✅ Certificate Management - PKI infrastructure
- ✅ Rule Engine - Route data to 40+ AWS services ($77,760/month alone)
- ✅ OTA Updates - Push firmware to device fleet
- ✅ Fleet Indexing - Search across all devices
- ✅ Jobs - Run commands on device groups
- ✅ Device Defender - Security auditing and anomaly detection
- ✅ Device Advisor - Testing suite for IoT devices

**With Google Cloud, you build all of this yourself** (or go without).

**The trade-off:**
- AWS = Pay for convenience and enterprise features
- Google = Pay for infrastructure, build features yourself
- Self-hosted = Pay for hardware, build everything yourself

#### 4. Designed for Different Scale

**AWS IoT Core Sweet Spot:**
```
Scale:          10 - 10,000 devices
Messages:       1 million - 1 billion/month
Monthly cost:   $10 - $10,000
Cost per device: $1 - $10/month

At 1,000 devices × 1 msg/min:
- Messages: ~43M/month
- Cost: ~$50/month (very reasonable)
- Premium features justify the cost
```

**Your Scale:**
```
Scale:          100,000 devices (10-100x beyond sweet spot)
Messages:       518.4 billion/month (518x above sweet spot)
Monthly cost:   $2,210,527 (not designed for this scale)
Cost per device: $22.11/month (too expensive at scale)
```

**Key Insight:** AWS IoT Core pricing assumes you need enterprise features for a manageable fleet. At 100K devices, the per-message costs become prohibitive.

### Cost Comparison: Messaging Only

| Platform | Per Million Messages | 518.4B Messages/Month | Multiple |
|----------|---------------------|----------------------|----------|
| Google Pub/Sub | $0.0028 | $1,446 | 1x (baseline) |
| Self-hosted MQTT | $0.0016 | $815 | 0.56x |
| Azure IoT Hub | $0.28 | $145,000 | 100x |
| AWS IoT Core | $1.00 | $518,400 | 358x |

### Cost Comparison: Storage (51.84 TB/month)

| Database | Storage Type | $/GB-month | Total Cost | Multiple |
|----------|--------------|-----------|------------|----------|
| S3 Glacier | Archive | $0.004 | $207 | 1x (baseline) |
| BigQuery | Columnar | $0.02 | $1,037 | 5x |
| Self-hosted SSD | SSD | $0.125 | $6,480 | 31x |
| DynamoDB | SSD | $0.25 | $12,960 | 63x |
| **Timestream (memory)** | **In-memory** | **$25.92** | **$1,342,848** | **6,487x** |

### The "Abstraction Premium"

```
Service Level              Monthly Cost    Cost/Sensor    Abstraction Level
─────────────────────────────────────────────────────────────────────────────
Self-hosted (bare metal)   $17,432        $0.17          You manage everything
Google Cloud (DIY IoT)     $7,505         $0.08          Managed infrastructure
Azure IoT Hub              $162,593       $1.63          Managed IoT platform
AWS IoT Core               $2,210,527     $22.11         Premium managed IoT

Abstraction premium: 127x difference between cheapest and most expensive
```

### When AWS IoT Core Makes Sense

Despite the high cost at your scale, AWS IoT Core is perfect when:

**1. Small Scale (10-1,000 devices)**
```
Example: 100 devices × 1 msg/min
- Messages: ~4.3M/month
- Cost: ~$4-10/month
- Excellent value for fully managed service
```

**2. Enterprise Features Are Critical**
- Need OTA firmware updates for device fleet
- Complex device provisioning workflows
- Fleet management and monitoring
- Security compliance (device certificates, auditing)
- Integration with existing AWS infrastructure

**3. Development Speed > Cost**
- Proof of concept / MVP phase
- Get to market in weeks instead of months
- Time-to-market is more valuable than infrastructure cost

**4. Deep AWS Ecosystem Integration**
- Already using Lambda, DynamoDB, S3, etc.
- Want native integration with AWS services
- Team expertise in AWS stack
- Tight integration worth the premium

### How to Use AWS More Cheaply

If you must use AWS but want to reduce costs, **skip IoT Core** and use lower-level services:

**Option A: AWS Kinesis + DynamoDB**
```
Kinesis Data Streams:
- ~100 shards × $0.015/hour × 720 = $1,080
- Data ingestion: 51.84 TB × $0.014/GB = $726

DynamoDB:
- Writes: 518.4B × $1.25/million = $648,000
- Storage: 51.84 TB × $0.25/GB = $12,960

Total: ~$663,000/month (70% cheaper than IoT Core, but still expensive)
```

**Option B: AWS MSK (Managed Kafka) + OpenSearch/DynamoDB**
```
MSK (Kafka):
- 3 brokers × kafka.m5.4xlarge × $1.40/hour × 720 = $3,024
- Storage: 100 TB × $0.10/GB = $10,000

DynamoDB (same as above): $661,000

Total: ~$674,000/month (similar to Kinesis option)
```

**Option C: EC2 Self-Managed on AWS**
```
MQTT Brokers: 5 × m5.2xlarge × $0.384/hour × 720 = $1,382
Database: 6 × r5.4xlarge × $1.008/hour × 720 = $4,355
Storage: 100 TB EBS SSD × $0.125/GB = $12,500
Load Balancer: ~$200
Bandwidth: ~$462

Total: ~$19,700/month (99% cheaper than IoT Core!)
```

**The lesson:** Even within AWS, using lower-level services is dramatically cheaper. The IoT Core premium is the convenience layer.

### Cost Comparison: Why Each Platform Costs What It Does

| Platform | Monthly Cost | Why This Price | What You're Paying For |
|----------|--------------|----------------|------------------------|
| **Google Cloud** | $7,505 | Commodity infrastructure | Message queue + data warehouse (no IoT abstraction) |
| **Self-hosted** | $17,432 | Raw infrastructure + labor | Servers + your DevOps team + your time |
| **Azure IoT Hub** | $162,593 | Moderate managed IoT | IoT platform + better time-series DB pricing |
| **AWS IoT Core** | $2,210,527 | Premium managed IoT | Enterprise IoT platform + expensive in-memory DB |

### The Bottom Line

AWS IoT Core is expensive at your scale because:

1. **Premium managed service pricing** - 358x more than Google Pub/Sub for messaging
2. **Timestream memory storage** - $1.3M/month alone, 1,295x more expensive than BigQuery
3. **Enterprise feature overhead** - Paying for features you may not need (OTA, fleet management, etc.)
4. **Designed for different scale** - Optimized for 10-10K devices, not 100K
5. **Optimization for ease, not cost** - Perfect for prototypes and small fleets, prohibitive at scale

**Key Insight:** The more abstraction/management you buy, the more you pay. At 100K sensors, you've outgrown premium managed IoT services and need:
- **Commodity cloud services** (Google Pub/Sub + BigQuery) = $7.5K/month (294x cheaper)
- **Or self-hosted** (Kafka + Clickhouse) = $17K/month TCO (127x cheaper)

---

## Scaling Strategy Roadmap

### Phase 1: Proof of Concept (1-10 customers)
**Recommended:** Google Cloud or Azure IoT
- **Cost:** $500-5,000/month
- **Duration:** 1-3 months
- **Focus:** Validate architecture, test edge cases, build MVP

### Phase 2: Growth (10-50 customers)
**Recommended:** Azure IoT (optimized) or start self-hosted PoC
- **Cost:** $5,000-40,000/month
- **Duration:** 6-12 months
- **Focus:** Optimize ingestion, implement caching, edge downsampling

### Phase 3: Scale (50-100 customers)
**Recommended:** Migrate to self-hosted for best economics
- **Cost:** $17,000-25,000/month
- **Duration:** Ongoing
- **Focus:** Geographic distribution, multi-region deployment

### Phase 4: Enterprise (100+ customers)
**Recommended:** Self-hosted Kafka + Clickhouse on bare metal
- **Cost:** Scales linearly, best margins
- **Focus:** Custom features, advanced analytics, global distribution

---

## Infrastructure Requirements at Scale

### MQTT Broker Requirements:
- Support 100,000 concurrent connections
- Handle 200,000 msg/sec sustained
- 400,000 msg/sec burst capacity
- TLS/SSL encryption
- QoS levels 0 or 1 (not 2 - too slow)
- Per-device authentication
- Topic-based routing (customer/sensor_id/data)

**Recommended:** EMQX Enterprise or Mosquitto cluster

### Time-Series Database Requirements:
- Write throughput: 200,000 writes/sec sustained
- Storage: 51.84 TB/month (1.728 TB/day)
- Query performance: <100ms for recent data
- Retention: 30 days hot, 90-365 days cold
- Downsampling: Aggregate older data (1-min, 1-hour averages)
- Replication: 3x for reliability

**Recommended:** TimescaleDB, Clickhouse, InfluxDB, AWS Timestream, Azure ADX

### Data Downsampling Strategy:
```
Real-time (2 readings/sec):     7 days = 12.096 TB
1-minute aggregates:            30 days = 1.728 TB (1/120th size)
1-hour aggregates:              365 days = 5.256 TB
──────────────────────────────────────────────────────
Total optimized storage:        ~19 TB vs 630 TB (97% reduction)
```

### Load Balancing:
- Geographic distribution (US-East, US-West, EU, Asia)
- Health checks every 10-30 seconds
- Automatic failover
- SSL termination
- DDoS protection (Cloudflare, AWS Shield)

### Backup & Disaster Recovery:
- Real-time replication to secondary region
- Daily snapshots to object storage (S3, GCS, Azure Blob)
- 30-day backup retention
- 4-hour RTO (Recovery Time Objective)
- 15-minute RPO (Recovery Point Objective)

---

## Recommendation for Custom UI Development

Since you want to build custom dashboards yourself, you need excellent APIs:

### Best Choice: Google Cloud (Pub/Sub + BigQuery)

**Why:**
- Excellent REST API for queries
- WebSocket support via Pub/Sub subscriptions
- SQL queries (familiar for developers)
- Most cost-effective ($7,505/month)
- CORS-friendly for web frontends

**Architecture for Custom UI:**
```
Backend:
  Raspberry Pi → MQTT Bridge → Pub/Sub → BigQuery + Bigtable
                                            ↓
                                    Custom API (FastAPI/Flask)
                                            ↓
Frontend:
  React/Vue/Svelte Dashboard with:
    - REST API for historical data
    - WebSocket for real-time updates
    - Custom charts (Chart.js/Recharts)
```

**API Examples:**

Historical data query:
```javascript
// Query last 1 hour of temperature data
const query = `
  SELECT timestamp, temperature, pressure
  FROM sensors.bmp280
  WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND sensor_id = 'sensor_123'
  ORDER BY timestamp DESC
`;
```

Real-time subscription:
```javascript
// Subscribe to live updates via Pub/Sub
const subscription = pubsub.subscription('sensor-data-realtime');
subscription.on('message', (message) => {
  const data = JSON.parse(message.data);
  updateDashboard(data);
});
```

---

## What NOT to Use

### ❌ AWS IoT Core + Timestream
- **Cost:** $2.2M/month
- **Why avoid:** 294x more expensive than Google Cloud
- **Only viable if:** Already deep in AWS ecosystem with enterprise budget

### ❌ InfluxDB Cloud (Usage-based)
- **Cost:** $1.05M/month
- **Why avoid:** Too expensive without enterprise negotiation
- **Alternative:** InfluxDB Dedicated with negotiated pricing ($50K-150K/month)

### ❌ ThingSpeak
- **Not viable:** Platform cannot handle 2 msg/sec per sensor
- **Limitations:** Max 1 message every 15 seconds
- **Designed for:** <100 sensors, hobbyist projects

---

## Key Decision Factors

### Choose Google Cloud if:
- ✅ Cost is primary concern
- ✅ You have development resources
- ✅ Analytics > real-time dashboards
- ✅ Comfortable building custom MQTT bridge
- ✅ Building custom UI (excellent APIs)

### Choose Azure IoT if:
- ✅ Want fully managed service
- ✅ Need native MQTT support
- ✅ Time-series analytics important
- ✅ Limited DevOps resources
- ✅ Can implement edge optimization

### Choose Self-Hosted if:
- ✅ Long-term project (3+ years)
- ✅ Have DevOps team in place
- ✅ Need lowest per-unit cost at scale
- ✅ Want full control and customization
- ✅ Growing beyond 100 customers
- ✅ Data sovereignty requirements

### Avoid AWS IoT Core at this scale:
- ❌ 30-200x more expensive than alternatives
- ❌ Only if already deep in AWS ecosystem
- ❌ Consider AWS alternatives (Kinesis + DynamoDB) instead

---

## Next Steps

To implement cloud integration for Rasperature project:

1. **Choose platform** based on your requirements
2. **Start with MVP** on chosen platform (Phase 1)
3. **Build MQTT publisher** to send BMP280 data to cloud
4. **Create REST API** for custom UI access
5. **Implement downsampling** at edge for cost optimization
6. **Build custom dashboard** with real-time + historical data
7. **Optimize costs** as you scale (caching, aggregation, etc.)

---

## Conclusion

For 100 customers × 1,000 sensors × 2 readings/second:

**Best immediate solution:** Google Cloud (Pub/Sub + BigQuery) at $7,505/month
- Most cost-effective cloud option
- Requires building MQTT bridge
- Excellent for custom UI development

**Best long-term solution:** Self-hosted (Bare Metal) at $17,432/month TCO
- Requires 6-month build + ongoing DevOps
- Best margins as you grow beyond 100 customers
- Complete control for custom features

**Best managed solution:** Azure IoT Hub + ADX (optimized) at $38,948/month
- Good balance of managed service and cost
- Native MQTT support
- Implement edge downsampling for optimization

**Recommended path:**
1. Start with Google Cloud for PoC/early customers
2. Optimize and implement downsampling strategy
3. At 30-50 customers, evaluate migration to self-hosted
4. By 100 customers, transition to bare metal for best economics

**Key insight:** At 100K sensors, you've outgrown premium managed IoT services. Use commodity cloud services or self-host for 20-300x cost savings.

---

*Analysis Date: January 2025*
*Based on pricing from AWS, Azure, Google Cloud, InfluxDB, and Hetzner*
