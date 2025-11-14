# Expert System Quick Start Guide

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**

## Installation (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/noone/repos/BBB

# Install core requirements
pip install numpy

# Install vector database (choose one or both)
pip install chromadb  # Recommended for production
pip install faiss-cpu  # Recommended for high performance

# Optional: Install all requirements at once
pip install -r requirements_expert_system.txt
```

### 2. Verify Installation

```bash
python -c "from blank_business_builder.expert_system import MultiDomainExpertSystem; print('✓ Expert system installed')"
```

## Quick Test (2 minutes)

### Run Demo

```bash
# Full comprehensive demo (6 demos, ~5 minutes)
python demo_expert_system.py

# Or run specific demos:
python -c "
import asyncio
from demo_expert_system import demo_1_basic_queries
asyncio.run(demo_1_basic_queries())
"
```

### Run Tests

```bash
# Run all tests
python test_expert_system.py

# Run with verbose output
python -m pytest test_expert_system.py -v
```

## Basic Usage (1 minute)

### Example 1: Single Expert Query

```python
import asyncio
from blank_business_builder.expert_system import (
    MultiDomainExpertSystem,
    ExpertQuery,
    ExpertDomain
)

async def query_expert():
    # Initialize system
    system = MultiDomainExpertSystem(use_chromadb=True)

    # Query chemistry expert
    query = ExpertQuery(
        query="What are chemical bonds?",
        domain=ExpertDomain.CHEMISTRY
    )

    response = await system.query(query)
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence:.2%}")

asyncio.run(query_expert())
```

### Example 2: Multi-Expert Ensemble

```python
async def query_ensemble():
    system = MultiDomainExpertSystem(use_chromadb=True)

    # Query multiple experts at once
    query = ExpertQuery(
        query="How does quantum mechanics apply to chemistry?",
        use_ensemble=True
    )

    response = await system.query(query)
    print(f"Consensus: {response.consensus_answer}")
    print(f"Agreement: {response.agreement_score:.2%}")
    print(f"Experts consulted: {len(response.individual_responses)}")

asyncio.run(query_ensemble())
```

### Example 3: Business Integration

```python
from blank_business_builder.expert_integration import (
    launch_expert_enhanced_business
)

async def launch_business():
    result = await launch_expert_enhanced_business(
        business_concept="Scientific Research Consulting",
        founder_name="Your Name",
        duration_hours=0.1,  # 6 minutes demo
        enable_experts=True
    )

    print(f"Revenue generated: ${result['metrics']['revenue']['total']:,.2f}")
    print(f"Expert consultations: {result['expert_system']['total_consultations']}")

asyncio.run(launch_business())
```

## Features at a Glance

✓ **4 Science Domains**: Chemistry, Biology, Physics, Materials Science
✓ **Vector RAG**: ChromaDB or FAISS for scalable retrieval
✓ **Ensemble Intelligence**: Multi-expert voting and consensus
✓ **Auto-Specialization**: Continuous learning from feedback
✓ **Fine-Tuning**: 5 training strategies (supervised, RL, meta-learning, etc.)
✓ **Business Integration**: Enhances BBB autonomous agents
✓ **Production Ready**: Persistent storage, caching, monitoring

## Next Steps

1. **Read Full Documentation**: `EXPERT_SYSTEM_README.md`
2. **Run Demos**: `python demo_expert_system.py`
3. **Explore API**: Check `src/blank_business_builder/expert_system.py`
4. **Add Your Domain**: Extend with custom expert classes
5. **Fine-Tune**: Use your own datasets for specialization

## Common Commands

```bash
# Quick demo
python demo_expert_system.py

# Run tests
python test_expert_system.py

# Query from command line
python -m blank_business_builder.expert_system

# Launch expert-enhanced business
python -m blank_business_builder.expert_integration "Your Business" "Your Name" 0.1

# Check system status
python -c "
import asyncio
from blank_business_builder.expert_system import MultiDomainExpertSystem
system = MultiDomainExpertSystem(use_chromadb=True)
print(system.get_system_status())
"
```

## Performance Tips

### For Speed
- Use FAISS instead of ChromaDB
- Enable GPU acceleration: `pip install faiss-gpu`
- Reduce embedding dimensions
- Implement caching

### For Accuracy
- Add more domain-specific knowledge documents
- Fine-tune experts on your datasets
- Use ensemble mode for critical queries
- Increase confidence thresholds

### For Scale
- Use ChromaDB for persistent storage
- Deploy multiple expert system instances
- Load balance queries across instances
- Batch similar queries together

## Troubleshooting

**Q: "No module named 'chromadb'"**
```bash
pip install chromadb
```

**Q: "FAISS import fails"**
```bash
pip install faiss-cpu  # or faiss-gpu
```

**Q: "Low confidence scores"**
- Add more knowledge documents to vector store
- Fine-tune experts with domain-specific datasets
- Check query formulation

**Q: "Slow queries"**
- Switch to FAISS: `MultiDomainExpertSystem(use_chromadb=False)`
- Enable caching
- Reduce max_results in queries

## Support

For issues, questions, or collaboration:
- Email: inventor@aios.is
- Website: https://aios.is
- GitHub: Check BBB repository

## What's Next?

We recommend:
1. Run the full demo to see all capabilities
2. Integrate with your BBB autonomous agents
3. Fine-tune experts on your domain data
4. Add custom domain experts for your business
5. Deploy to production with monitoring

Happy building! 🚀
