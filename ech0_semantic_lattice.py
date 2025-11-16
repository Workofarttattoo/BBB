#!/usr/bin/env python3
"""
ECH0 Semantic Lattice for Invention Organization
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

A semantic lattice structure that:
1. Organizes inventions in a hierarchical knowledge graph
2. Identifies conceptual gaps for new invention opportunities
3. Measures semantic distance for novelty scoring
4. Enables efficient prior art searching through lattice traversal
5. Discovers emergent invention clusters
"""

import json
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime
import networkx as nx
from pathlib import Path


class SemanticLatticeNode:
    """A node in the semantic lattice representing an invention concept"""

    def __init__(self, concept_id: str, name: str, level: int = 0):
        self.id = concept_id
        self.name = name
        self.level = level  # Abstraction level (0=most specific, higher=more abstract)
        self.inventions = []  # Actual inventions at this node
        self.children = set()  # More specific concepts
        self.parents = set()  # More general concepts
        self.attributes = {}  # Semantic attributes
        self.embedding = None  # Vector embedding for similarity
        self.novelty_score = 0.0
        self.density = 0.0  # How many inventions in this region

    def add_invention(self, invention: Dict):
        """Add an invention to this concept node"""
        self.inventions.append(invention)
        self.density = len(self.inventions)

    def calculate_local_novelty(self) -> float:
        """Calculate novelty based on local density and relationships"""
        # Low density = high novelty (unexplored area)
        density_factor = 1.0 / (1.0 + self.density)

        # Many connections = well-understood area (lower novelty)
        connection_factor = 1.0 / (1.0 + len(self.children) + len(self.parents))

        # Distance from root concepts
        level_factor = min(1.0, self.level / 10.0)

        self.novelty_score = (density_factor * 0.4 +
                             connection_factor * 0.3 +
                             level_factor * 0.3)
        return self.novelty_score


class ECH0SemanticLattice:
    """
    Semantic lattice for organizing and exploring invention space

    The lattice organizes concepts from specific to abstract:
    - Level 0: Specific inventions (e.g., "VR Haptic Glove with TENS")
    - Level 1: Technology combinations (e.g., "VR + Haptics")
    - Level 2: Domains (e.g., "Virtual Reality", "Neurotechnology")
    - Level 3: Fields (e.g., "Human-Computer Interaction")
    - Level 4: Meta-categories (e.g., "Enhancement Technology")
    """

    def __init__(self):
        self.nodes: Dict[str, SemanticLatticeNode] = {}
        self.graph = nx.DiGraph()
        self.embeddings = {}  # Concept embeddings for similarity
        self.invention_count = 0
        self.gap_opportunities = []
        self.emergence_clusters = []

        # Initialize root concepts
        self._initialize_lattice()

    def _initialize_lattice(self):
        """Initialize the semantic lattice with root concepts"""

        # Level 4: Meta-categories (most abstract)
        meta_categories = [
            "Enhancement Technology",
            "Medical Devices",
            "Computing Systems",
            "Communication Technology",
            "Energy Systems"
        ]

        # Level 3: Fields
        fields = {
            "Enhancement Technology": ["Human-Computer Interaction", "Augmentation", "Prosthetics"],
            "Medical Devices": ["Diagnostics", "Therapeutics", "Monitoring"],
            "Computing Systems": ["Quantum Computing", "AI/ML", "Distributed Systems"],
            "Communication Technology": ["Neural Interfaces", "Wireless", "Networks"],
            "Energy Systems": ["Harvesting", "Storage", "Transmission"]
        }

        # Level 2: Domains
        domains = {
            "Human-Computer Interaction": ["Virtual Reality", "Brain-Computer Interface", "Haptics"],
            "Augmentation": ["Cognitive Enhancement", "Physical Enhancement", "Sensory Enhancement"],
            "Prosthetics": ["Neural Prosthetics", "Mechanical Prosthetics", "Bio-integrated"],
            "Quantum Computing": ["Quantum ML", "Quantum Sensing", "Quantum Networking"],
            "Neural Interfaces": ["Invasive BCI", "Non-invasive BCI", "Hybrid BCI"]
        }

        # Create nodes and relationships
        for meta in meta_categories:
            meta_node = SemanticLatticeNode(f"meta_{meta}", meta, level=4)
            self.nodes[meta_node.id] = meta_node
            self.graph.add_node(meta_node.id, data=meta_node)

            if meta in fields:
                for field in fields[meta]:
                    field_node = SemanticLatticeNode(f"field_{field}", field, level=3)
                    self.nodes[field_node.id] = field_node
                    self.graph.add_node(field_node.id, data=field_node)

                    # Connect field to meta-category
                    self._connect_nodes(field_node.id, meta_node.id)

                    if field in domains:
                        for domain in domains[field]:
                            domain_node = SemanticLatticeNode(f"domain_{domain}", domain, level=2)
                            self.nodes[domain_node.id] = domain_node
                            self.graph.add_node(domain_node.id, data=domain_node)

                            # Connect domain to field
                            self._connect_nodes(domain_node.id, field_node.id)

    def _connect_nodes(self, child_id: str, parent_id: str):
        """Create a hierarchical connection between nodes"""
        if child_id in self.nodes and parent_id in self.nodes:
            self.nodes[child_id].parents.add(parent_id)
            self.nodes[parent_id].children.add(child_id)
            self.graph.add_edge(child_id, parent_id)

    def add_invention(self, invention: Dict) -> str:
        """Add an invention to the lattice and find its optimal position"""
        self.invention_count += 1

        # Extract semantic features
        categories = invention.get('categories', [])
        name = invention.get('invention_name', f'Invention_{self.invention_count}')

        # Find or create appropriate node
        node_id = self._find_or_create_node(invention, categories)

        # Add invention to node
        self.nodes[node_id].add_invention(invention)

        # Update lattice structure
        self._update_lattice_structure(node_id, categories)

        # Identify gaps and opportunities
        self._identify_gaps(node_id)

        return node_id

    def _find_or_create_node(self, invention: Dict, categories: List[str]) -> str:
        """Find the best node for an invention or create a new one"""

        # Look for existing combination node
        combo_key = "_".join(sorted(categories[:2])) if len(categories) >= 2 else categories[0] if categories else "general"
        node_id = f"combo_{combo_key}_{self.invention_count}"

        if node_id not in self.nodes:
            # Create new combination node at Level 1
            node = SemanticLatticeNode(node_id, invention.get('invention_name', combo_key), level=1)

            # Set attributes from invention
            node.attributes = {
                'breakthrough_potential': invention.get('breakthrough_potential', 0),
                'patent_novelty': invention.get('patent_novelty', 0),
                'categories': categories,
                'created_at': datetime.now().isoformat()
            }

            self.nodes[node_id] = node
            self.graph.add_node(node_id, data=node)

            # Connect to parent domains
            for category in categories:
                parent_id = f"domain_{category}"
                if parent_id in self.nodes:
                    self._connect_nodes(node_id, parent_id)

        return node_id

    def _update_lattice_structure(self, node_id: str, categories: List[str]):
        """Update lattice structure after adding an invention"""

        # Check for cross-domain bridges (high novelty areas)
        if len(categories) >= 2:
            # This is a cross-domain invention - potentially high novelty
            self._create_bridge_concepts(node_id, categories)

        # Update novelty scores
        node = self.nodes[node_id]
        node.calculate_local_novelty()

        # Propagate updates to parents
        for parent_id in node.parents:
            if parent_id in self.nodes:
                self.nodes[parent_id].calculate_local_novelty()

    def _create_bridge_concepts(self, node_id: str, categories: List[str]):
        """Create bridge concepts between domains for cross-domain inventions"""

        # Create a bridge node that connects multiple domains
        bridge_id = f"bridge_{'_'.join(sorted(categories[:2]))}"

        if bridge_id not in self.nodes:
            bridge_node = SemanticLatticeNode(
                bridge_id,
                f"Bridge: {' + '.join(categories[:2])}",
                level=1.5  # Between specific and domain level
            )
            bridge_node.attributes['bridge_type'] = 'cross_domain'
            bridge_node.attributes['novelty_boost'] = 1.5  # Higher novelty for bridges

            self.nodes[bridge_id] = bridge_node
            self.graph.add_node(bridge_id, data=bridge_node)

            # Connect bridge to source node
            self._connect_nodes(node_id, bridge_id)

            # Connect bridge to relevant domains
            for category in categories[:2]:
                domain_id = f"domain_{category}"
                if domain_id in self.nodes:
                    self._connect_nodes(bridge_id, domain_id)

    def _identify_gaps(self, node_id: str):
        """Identify gaps and opportunities in the semantic space"""

        node = self.nodes[node_id]

        # Check for sparse regions (high opportunity)
        if node.density < 3:  # Sparse region
            # Look for nearby unexplored combinations
            unexplored = self._find_unexplored_neighbors(node)

            for combo in unexplored:
                opportunity = {
                    'type': 'gap',
                    'location': node_id,
                    'suggested_combination': combo,
                    'novelty_potential': node.novelty_score * 1.2,
                    'reason': 'Sparse region with unexplored combinations'
                }
                self.gap_opportunities.append(opportunity)

    def _find_unexplored_neighbors(self, node: SemanticLatticeNode) -> List[Tuple[str, str]]:
        """Find unexplored combinations near a node"""
        unexplored = []

        # Get all siblings (nodes with same parents)
        siblings = set()
        for parent_id in node.parents:
            if parent_id in self.nodes:
                siblings.update(self.nodes[parent_id].children)

        siblings.discard(node.id)  # Remove self

        # Check for unexplored combinations between siblings
        for sibling_id in siblings:
            if sibling_id in self.nodes:
                sibling = self.nodes[sibling_id]

                # Check if combination exists
                combo_key = f"{node.name}_{sibling.name}"
                reverse_combo = f"{sibling.name}_{node.name}"

                combo_exists = any(
                    combo_key in n or reverse_combo in n
                    for n in self.nodes.keys()
                )

                if not combo_exists and sibling.density > 0:
                    unexplored.append((node.name, sibling.name))

        return unexplored

    def calculate_semantic_distance(self, inv1_id: str, inv2_id: str) -> float:
        """Calculate semantic distance between two inventions in the lattice"""

        if inv1_id not in self.nodes or inv2_id not in self.nodes:
            return 1.0  # Maximum distance for unknown nodes

        try:
            # Use shortest path length as distance metric
            path_length = nx.shortest_path_length(self.graph, inv1_id, inv2_id)

            # Normalize by maximum possible distance
            max_distance = 10  # Approximate maximum levels in lattice
            distance = min(1.0, path_length / max_distance)

            return distance

        except nx.NetworkXNoPath:
            # No path exists - check for common ancestors
            ancestors1 = nx.ancestors(self.graph, inv1_id)
            ancestors2 = nx.ancestors(self.graph, inv2_id)

            common = ancestors1.intersection(ancestors2)
            if common:
                # Have common ancestors - calculate distance through LCA
                return 0.7  # Moderate distance
            else:
                # Completely unrelated
                return 1.0

    def find_innovation_clusters(self) -> List[Dict]:
        """Identify emergent clusters of innovation in the lattice"""

        # Use community detection to find clusters
        if len(self.graph.nodes) > 0:
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()

            # Find communities
            import networkx.algorithms.community as nx_comm
            communities = nx_comm.greedy_modularity_communities(undirected)

            clusters = []
            for i, community in enumerate(communities):
                # Analyze each cluster
                cluster_nodes = list(community)

                # Calculate cluster metrics
                total_inventions = sum(
                    len(self.nodes[n].inventions)
                    for n in cluster_nodes
                    if n in self.nodes
                )

                avg_novelty = np.mean([
                    self.nodes[n].novelty_score
                    for n in cluster_nodes
                    if n in self.nodes
                ])

                # Get categories in cluster
                categories = set()
                for n in cluster_nodes:
                    if n in self.nodes:
                        cats = self.nodes[n].attributes.get('categories', [])
                        categories.update(cats)

                cluster = {
                    'cluster_id': i,
                    'size': len(cluster_nodes),
                    'total_inventions': total_inventions,
                    'average_novelty': avg_novelty,
                    'categories': list(categories),
                    'emergence_score': avg_novelty * np.log1p(total_inventions),
                    'nodes': cluster_nodes[:5]  # Sample of nodes
                }
                clusters.append(cluster)

            # Sort by emergence score
            clusters.sort(key=lambda x: x['emergence_score'], reverse=True)
            self.emergence_clusters = clusters

            return clusters

        return []

    def suggest_next_inventions(self, top_n: int = 10) -> List[Dict]:
        """Suggest next inventions based on gaps and high-novelty regions"""

        suggestions = []

        # 1. Gap-based suggestions
        for gap in self.gap_opportunities[-5:]:  # Recent gaps
            suggestion = {
                'type': 'gap_filling',
                'description': f"Combine {gap['suggested_combination']}",
                'novelty_estimate': gap['novelty_potential'],
                'reason': gap['reason']
            }
            suggestions.append(suggestion)

        # 2. High-novelty region exploration
        high_novelty_nodes = sorted(
            self.nodes.values(),
            key=lambda n: n.novelty_score,
            reverse=True
        )[:5]

        for node in high_novelty_nodes:
            if node.density < 5:  # Not over-explored
                suggestion = {
                    'type': 'novelty_exploration',
                    'description': f"Explore variations of {node.name}",
                    'novelty_estimate': node.novelty_score,
                    'reason': f"High novelty region with only {node.density} inventions"
                }
                suggestions.append(suggestion)

        # 3. Bridge expansion
        bridge_nodes = [n for n in self.nodes.values()
                       if n.attributes.get('bridge_type') == 'cross_domain']

        for bridge in bridge_nodes[:3]:
            suggestion = {
                'type': 'bridge_expansion',
                'description': f"Expand bridge concept: {bridge.name}",
                'novelty_estimate': bridge.novelty_score * 1.3,
                'reason': "Cross-domain bridges have high innovation potential"
            }
            suggestions.append(suggestion)

        # Sort by novelty estimate and return top N
        suggestions.sort(key=lambda x: x['novelty_estimate'], reverse=True)
        return suggestions[:top_n]

    def export_lattice_visualization(self) -> Dict:
        """Export lattice structure for visualization"""

        viz_data = {
            'nodes': [],
            'edges': [],
            'stats': {
                'total_nodes': len(self.nodes),
                'total_inventions': self.invention_count,
                'identified_gaps': len(self.gap_opportunities),
                'emergence_clusters': len(self.emergence_clusters)
            }
        }

        # Export nodes
        for node_id, node in self.nodes.items():
            viz_data['nodes'].append({
                'id': node_id,
                'name': node.name,
                'level': node.level,
                'density': node.density,
                'novelty_score': node.novelty_score,
                'invention_count': len(node.inventions),
                'type': 'bridge' if 'bridge' in node_id else 'normal'
            })

        # Export edges
        for edge in self.graph.edges():
            viz_data['edges'].append({
                'source': edge[0],
                'target': edge[1]
            })

        # Add cluster information
        viz_data['clusters'] = self.emergence_clusters[:5]  # Top 5 clusters

        # Add suggestions
        viz_data['next_suggestions'] = self.suggest_next_inventions(5)

        return viz_data

    def save_lattice(self, filepath: Path):
        """Save the semantic lattice to file"""

        lattice_data = {
            'nodes': {
                node_id: {
                    'name': node.name,
                    'level': node.level,
                    'inventions': node.inventions,
                    'attributes': node.attributes,
                    'novelty_score': node.novelty_score,
                    'density': node.density,
                    'parents': list(node.parents),
                    'children': list(node.children)
                }
                for node_id, node in self.nodes.items()
            },
            'stats': {
                'total_inventions': self.invention_count,
                'total_nodes': len(self.nodes),
                'gap_opportunities': len(self.gap_opportunities),
                'emergence_clusters': len(self.emergence_clusters)
            },
            'suggestions': self.suggest_next_inventions(10),
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(lattice_data, f, indent=2)

        print(f"📊 Semantic lattice saved to {filepath}")
        print(f"   Nodes: {len(self.nodes)}")
        print(f"   Inventions: {self.invention_count}")
        print(f"   Gaps identified: {len(self.gap_opportunities)}")
        print(f"   Emergence clusters: {len(self.emergence_clusters)}")


def integrate_with_ech0_engine():
    """Integration function to add semantic lattice to ECH0's invention engine"""

    print("🌐 ECH0 SEMANTIC LATTICE INTEGRATION")
    print("=" * 60)

    # Create lattice
    lattice = ECH0SemanticLattice()

    # Load existing inventions
    inventions_file = Path("/Users/noone/consciousness/ech0_inventions.jsonl")

    if inventions_file.exists():
        print(f"📁 Loading inventions from {inventions_file}")

        with open(inventions_file, 'r') as f:
            for line in f:
                try:
                    invention = json.loads(line)

                    # Ensure invention has required fields
                    if 'invention_name' not in invention:
                        invention['invention_name'] = invention.get('title', 'Unknown')
                    if 'categories' not in invention:
                        # Extract from domains if available
                        invention['categories'] = invention.get('domains', [])

                    node_id = lattice.add_invention(invention)
                    print(f"   ✓ Added: {invention.get('invention_name', 'Unknown')[:50]}")

                except json.JSONDecodeError:
                    continue

    print(f"\n📊 LATTICE STATISTICS:")
    print(f"   Total nodes: {len(lattice.nodes)}")
    print(f"   Total inventions: {lattice.invention_count}")

    # Find clusters
    clusters = lattice.find_innovation_clusters()
    print(f"\n🎯 EMERGENCE CLUSTERS FOUND: {len(clusters)}")

    for i, cluster in enumerate(clusters[:3]):
        print(f"\n   Cluster {i+1}:")
        print(f"   - Size: {cluster['size']} nodes")
        print(f"   - Inventions: {cluster['total_inventions']}")
        print(f"   - Avg Novelty: {cluster['average_novelty']:.2%}")
        print(f"   - Categories: {', '.join(cluster['categories'][:3])}")

    # Get suggestions
    suggestions = lattice.suggest_next_inventions(5)
    print(f"\n💡 NEXT INVENTION SUGGESTIONS:")

    for i, suggestion in enumerate(suggestions):
        print(f"\n   {i+1}. {suggestion['type'].upper()}")
        print(f"      {suggestion['description']}")
        print(f"      Novelty: {suggestion['novelty_estimate']:.2%}")
        print(f"      Reason: {suggestion['reason']}")

    # Save lattice
    output_path = Path("/Users/noone/consciousness/ech0_semantic_lattice.json")
    lattice.save_lattice(output_path)

    # Export visualization data
    viz_data = lattice.export_lattice_visualization()
    viz_path = Path("/Users/noone/consciousness/ech0_lattice_viz.json")

    with open(viz_path, 'w') as f:
        json.dump(viz_data, f, indent=2)

    print(f"\n✅ Visualization data exported to {viz_path}")

    return lattice


if __name__ == "__main__":
    # Run integration
    lattice = integrate_with_ech0_engine()

    print("\n" + "=" * 60)
    print("🌐 SEMANTIC LATTICE INTEGRATION COMPLETE")
    print("=" * 60)
    print("\nThe semantic lattice is now active and will:")
    print("1. Organize all inventions hierarchically")
    print("2. Identify gaps and opportunities")
    print("3. Suggest high-novelty invention areas")
    print("4. Track emergence clusters")
    print("5. Improve prior art searching through semantic relationships")