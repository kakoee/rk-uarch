use crate::Error;
#[derive(Debug, Clone, Copy)]
pub enum Direction {
    Positive,
    Negative,
}
/// Independent instances represent independent NoCs. No link timing is modeled at K1.
#[derive(Debug)]
pub struct Topology {
    offsets: Vec<usize>,
    adjacency: Vec<u32>,
    routes: Vec<Vec<u32>>,
    nodes: u32,
}
impl Topology {
    pub fn new(width: u32, height: u32, torus: bool, direction: Direction) -> Result<Self, Error> {
        let nodes = width
            .checked_mul(height)
            .filter(|&v| v > 0)
            .ok_or(Error::InvalidRoute)?;
        let mut offsets = vec![0];
        let mut adjacency = Vec::new();
        for node in 0..nodes {
            let (x, y) = (node % width, node / width);
            let mut neighbors = Vec::new();
            if x > 0 {
                neighbors.push(node - 1);
            } else if torus {
                neighbors.push(node + width - 1);
            }
            if x + 1 < width {
                neighbors.push(node + 1);
            } else if torus {
                neighbors.push(node + 1 - width);
            }
            if y > 0 {
                neighbors.push(node - width);
            } else if torus {
                neighbors.push(node + (height - 1) * width);
            }
            if y + 1 < height {
                neighbors.push(node + width);
            } else if torus {
                neighbors.push(x);
            }
            neighbors.retain(|&n| n != node);
            neighbors.sort_unstable();
            neighbors.dedup();
            adjacency.extend(neighbors);
            offsets.push(adjacency.len());
        }
        let mut routes = Vec::new();
        for from in 0..nodes {
            for to in 0..nodes {
                let (mut x, mut y) = (from % width, from / width);
                let mut route = vec![from];
                for axis in 0..2 {
                    let (mut current, dest, size) = if axis == 0 {
                        (x, to % width, width)
                    } else {
                        (y, to / width, height)
                    };
                    while current != dest {
                        let positive = if torus {
                            let plus = (u64::from(dest) + u64::from(size) - u64::from(current))
                                % u64::from(size);
                            let minus = u64::from(size) - plus;
                            plus < minus
                                || (plus == minus && matches!(direction, Direction::Positive))
                        } else {
                            current < dest
                        };
                        current = if positive {
                            if current + 1 == size { 0 } else { current + 1 }
                        } else if current == 0 {
                            size - 1
                        } else {
                            current - 1
                        };
                        if axis == 0 {
                            x = current;
                        } else {
                            y = current;
                        }
                        route.push(y * width + x);
                    }
                }
                routes.push(route);
            }
        }
        Ok(Self {
            offsets,
            adjacency,
            routes,
            nodes,
        })
    }
    pub fn nodes(&self) -> u32 {
        self.nodes
    }
    pub fn neighbors(&self, node: u32) -> &[u32] {
        if node >= self.nodes {
            return &[];
        }
        &self.adjacency[self.offsets[node as usize]..self.offsets[node as usize + 1]]
    }
    pub fn route(&self, from: u32, to: u32) -> Result<Vec<u32>, Error> {
        if from >= self.nodes || to >= self.nodes {
            return Err(Error::InvalidRoute);
        }
        Ok(self.routes[from as usize * self.nodes as usize + to as usize].clone())
    }
}
