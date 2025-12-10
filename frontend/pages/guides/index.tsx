import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Search, Wrench, BookOpen, Zap, Plus, Filter, ArrowLeft } from 'lucide-react';

interface Tutorial {
  id: number;
  brand: string;
  model: string;
  issue_type: string;
  title: string;
  difficulty: string;
  source: string;
}

// Brand data with logos and info
const BRANDS = [
  {
    id: 'lenovo',
    name: 'Lenovo',
    logo: '/brands/lenovo.svg',
    color: '#E2231A',
    models: 25,
    guides: 150
  },
  {
    id: 'dell',
    name: 'Dell',
    logo: '/brands/dell.svg',
    color: '#007DB8',
    models: 30,
    guides: 200
  },
  {
    id: 'hp',
    name: 'HP',
    logo: '/brands/hp.svg',
    color: '#0096D6',
    models: 28,
    guides: 180
  },
  {
    id: 'asus',
    name: 'Asus',
    logo: '/brands/asus.svg',
    color: '#000000',
    models: 22,
    guides: 120
  },
  {
    id: 'acer',
    name: 'Acer',
    logo: '/brands/acer.svg',
    color: '#83B81A',
    models: 18,
    guides: 90
  },
  {
    id: 'msi',
    name: 'MSI',
    logo: '/brands/msi.svg',
    color: '#FF0000',
    models: 15,
    guides: 75
  }
];

const GUIDE_CATEGORIES = [
  {
    id: 'laptop',
    name: 'Laptops',
    icon: Wrench,
    description: 'Laptop repair and troubleshooting guides',
    color: 'text-blue-500'
  },
  {
    id: 'desktop',
    name: 'Desktop PCs',
    icon: Zap,
    description: 'Desktop computer repair guides',
    color: 'text-green-500'
  },
  {
    id: 'mac',
    name: 'MacBooks',
    icon: BookOpen,
    description: 'Apple MacBook repair guides',
    color: 'text-purple-500'
  },
  {
    id: 'phone',
    name: 'Phones',
    icon: Plus,
    description: 'Smartphone repair guides',
    color: 'text-amber-500'
  }
];

export default function BrowseGuides() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(null);
  const [filteredBrands, setFilteredBrands] = useState(BRANDS);
  const [tutorials, setTutorials] = useState<Tutorial[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    if (searchQuery) {
      const filtered = BRANDS.filter(brand =>
        brand.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredBrands(filtered);
    } else {
      setFilteredBrands(BRANDS);
    }
  }, [searchQuery]);

  useEffect(() => {
    if (selectedCategory) {
      fetchTutorials();
    }
  }, [selectedCategory, selectedBrand, selectedDifficulty, searchQuery]);

  const fetchTutorials = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      // Add category filter with ID ranges
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedBrand) params.append('brand', selectedBrand);
      if (selectedDifficulty) params.append('difficulty', selectedDifficulty);
      if (searchQuery) params.append('search', searchQuery);
      
      params.append('limit', '50');
      
      console.log('[API] Fetching tutorials with params:', Object.fromEntries(params));
      const response = await fetch(`http://localhost:8000/api/tutorials?${params}`);
      const data = await response.json();
      console.log('API Response:', data);
      console.log('First tutorial:', data.tutorials?.[0]);
      setTutorials(data.tutorials || []);
      setTotalCount(data.total || 0);
    } catch (error) {
      console.error('Error fetching tutorials:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy': return 'success';
      case 'medium': return 'warning';
      case 'hard': return 'danger';
      default: return 'default';
    }
  };

  const handleBrandClick = (brandId: string) => {
    router.push(`/guides/${brandId}`);
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(categoryId);
    setTimeout(() => {
      const section = document.getElementById('tutorials-section');
      if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Repair Guides Library
            </h1>
            <p className="text-xl text-neutral-300 mb-8 max-w-2xl mx-auto">
              Browse thousands of free repair guides for laptops from all major brands
            </p>

            {/* Search Bar */}
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 w-5 h-5" />
                <Input
                  type="text"
                  placeholder="Search by brand, model, or issue..."
                  value={searchQuery}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                  className="pl-12 h-14 text-lg bg-white text-neutral-900"
                />
              </div>
            </div>

            {/* Stats */}
            <div className="mt-12 grid grid-cols-3 gap-8 max-w-2xl mx-auto">
              <div>
                <div className="text-3xl font-bold text-blue-400">138</div>
                <div className="text-sm text-neutral-400 mt-1">Device Models</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-400">815</div>
                <div className="text-sm text-neutral-400 mt-1">Repair Guides</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-400">2.4k</div>
                <div className="text-sm text-neutral-400 mt-1">Community Contributions</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        
        {/* Guide Categories */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-neutral-900 mb-6">
            Browse by Category
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {GUIDE_CATEGORIES.map((category) => (
              <Card
                key={category.id}
                hover
                onClick={() => handleCategoryClick(category.id)}
                className="cursor-pointer border-2 border-transparent hover:border-neutral-900 transition-all"
              >
                <CardContent className="p-6 text-center">
                  <category.icon className={`w-12 h-12 mx-auto mb-4 ${category.color}`} />
                  <h3 className="font-semibold text-neutral-900 mb-2">
                    {category.name}
                  </h3>
                  <p className="text-sm text-neutral-600">
                    {category.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Tutorials Section */}
        <section id="tutorials-section">
          {selectedCategory && (
            <div className="space-y-4 mb-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-neutral-900">
                    {selectedCategory.charAt(0).toUpperCase() + selectedCategory.slice(1).replace('_', ' ')} Tutorials
                  </h2>
                  <p className="text-neutral-600 mt-1">{totalCount} tutorials found</p>
                </div>
                <Button
                  variant="outline"
                  onClick={() => { setSelectedCategory(null); setTutorials([]); }}
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Categories
                </Button>
              </div>
              {/* Filters */}
              <div className="flex flex-wrap gap-2">
                <select
                  value={selectedBrand || ''}
                  onChange={(e) => setSelectedBrand(e.target.value || null)}
                  className="px-4 py-2 border border-neutral-300 rounded-lg bg-white text-sm"
                >
                  <option value="">All Brands</option>
                  {BRANDS.map(brand => (
                    <option key={brand.id} value={brand.id}>{brand.name}</option>
                  ))}
                </select>

                <select
                  value={selectedDifficulty || ''}
                  onChange={(e) => setSelectedDifficulty(e.target.value || null)}
                  className="px-4 py-2 border border-neutral-300 rounded-lg bg-white text-sm"
                >
                  <option value="">All Difficulties</option>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              {/* Tutorials Grid */}
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-4 text-neutral-600">Loading tutorials...</p>
                </div>
              ) : tutorials.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {tutorials.map((tutorial) => {
                    if (!tutorial?.id) {
                      console.error('Tutorial missing ID:', tutorial);
                      return null;
                    }
                    return (
                    <Card
                      key={tutorial.id}
                      hover
                      onClick={() => {
                        console.log('Clicking tutorial:', tutorial.id);
                        router.push(`/tutorial/${tutorial.id}`);
                      }}
                      className="cursor-pointer"
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <Badge variant={getDifficultyColor(tutorial.difficulty)}>
                            {tutorial.difficulty}
                          </Badge>
                          <Badge variant="default">
                            {tutorial.source}
                          </Badge>
                        </div>
                        <CardTitle className="text-base line-clamp-2">
                          {tutorial.title}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="default" className="capitalize">
                            {tutorial.brand}
                          </Badge>
                          <Badge variant="default" className="capitalize">
                            {tutorial.issue_type}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  );
                  })}
                </div>
              ) : (
                <Card>
                  <CardContent className="p-12 text-center">
                    <Search className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
                    <p className="text-neutral-600">No tutorials found with the selected filters</p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </section>

        {/* Brand Selection */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-neutral-900">
              Select Your Laptop Brand
            </h2>
            <Badge variant="default">
              {filteredBrands.length} brands
            </Badge>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {filteredBrands.map((brand) => (
              <Card
                key={brand.id}
                hover
                onClick={() => handleBrandClick(brand.id)}
                className="cursor-pointer group"
              >
                <CardContent className="p-6">
                  {/* Brand Logo */}
                  <div className="aspect-square bg-white rounded-lg flex items-center justify-center mb-4 border border-neutral-200 group-hover:border-neutral-900 transition-colors">
                    <div 
                      className="text-4xl font-bold"
                      style={{ color: brand.color }}
                    >
                      {brand.name.charAt(0)}
                    </div>
                  </div>

                  {/* Brand Name */}
                  <h3 className="font-semibold text-neutral-900 mb-2 text-center">
                    {brand.name}
                  </h3>

                  {/* Stats */}
                  <div className="flex justify-between text-xs text-neutral-600">
                    <span>{brand.models} models</span>
                    <span>{brand.guides} guides</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Call to Action - Community Guides */}
        <section className="mt-16">
          <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
            <CardContent className="p-8 text-center">
              <div className="max-w-2xl mx-auto">
                <Plus className="w-12 h-12 mx-auto mb-4 text-purple-600" />
                <h3 className="text-2xl font-bold text-neutral-900 mb-2">
                  Share Your Repair Knowledge
                </h3>
                <p className="text-neutral-600 mb-6">
                  Help others by contributing your own step-by-step repair guides with photos
                </p>
                <button
                  onClick={() => router.push('/guides/create')}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  Create a Guide
                </button>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
