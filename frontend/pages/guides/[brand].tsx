import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Card, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';
import { ArrowLeft, Search, Laptop, Calendar, TrendingUp } from 'lucide-react';

// Mock data - will be replaced with API calls
const BRAND_DATA: Record<string, any> = {
  lenovo: {
    name: 'Lenovo',
    color: '#E2231A',
    description: 'ThinkPad, IdeaPad, Legion gaming laptops',
    models: [
      {
        id: 'thinkpad-x1-carbon',
        name: 'ThinkPad X1 Carbon',
        series: 'ThinkPad X Series',
        image: '/models/lenovo-x1.jpg',
        guides: 45,
        difficulty: 'Medium',
        popularity: 95,
        year: '2023'
      },
      {
        id: 'ideapad-5',
        name: 'IdeaPad 5',
        series: 'IdeaPad Series',
        image: '/models/lenovo-ideapad5.jpg',
        guides: 32,
        difficulty: 'Easy',
        popularity: 88,
        year: '2022'
      },
      {
        id: 'legion-5-pro',
        name: 'Legion 5 Pro',
        series: 'Legion Gaming',
        image: '/models/lenovo-legion5.jpg',
        guides: 28,
        difficulty: 'Medium',
        popularity: 82,
        year: '2023'
      },
      {
        id: 'thinkpad-t14',
        name: 'ThinkPad T14',
        series: 'ThinkPad T Series',
        image: '/models/lenovo-t14.jpg',
        guides: 38,
        difficulty: 'Easy',
        popularity: 90,
        year: '2023'
      }
    ]
  },
  dell: {
    name: 'Dell',
    color: '#007DB8',
    description: 'XPS, Latitude, Inspiron, Alienware',
    models: [
      {
        id: 'xps-13-9310',
        name: 'XPS 13 9310',
        series: 'XPS Series',
        image: '/models/dell-xps13.jpg',
        guides: 52,
        difficulty: 'Hard',
        popularity: 96,
        year: '2023'
      },
      {
        id: 'xps-15-9500',
        name: 'XPS 15 9500',
        series: 'XPS Series',
        image: '/models/dell-xps15.jpg',
        guides: 48,
        difficulty: 'Medium',
        popularity: 93,
        year: '2023'
      },
      {
        id: 'latitude-7400',
        name: 'Latitude 7400',
        series: 'Latitude Series',
        image: '/models/dell-latitude.jpg',
        guides: 41,
        difficulty: 'Easy',
        popularity: 85,
        year: '2022'
      }
    ]
  },
  hp: {
    name: 'HP',
    color: '#0096D6',
    description: 'Pavilion, Envy, EliteBook, Omen',
    models: [
      {
        id: 'pavilion-15',
        name: 'Pavilion 15',
        series: 'Pavilion Series',
        image: '/models/hp-pavilion.jpg',
        guides: 36,
        difficulty: 'Easy',
        popularity: 87,
        year: '2023'
      },
      {
        id: 'envy-x360',
        name: 'Envy x360',
        series: 'Envy Series',
        image: '/models/hp-envy.jpg',
        guides: 29,
        difficulty: 'Medium',
        popularity: 81,
        year: '2023'
      }
    ]
  },
  asus: {
    name: 'Asus',
    color: '#000000',
    description: 'ZenBook, VivoBook, ROG gaming',
    models: [
      {
        id: 'zenbook-14',
        name: 'ZenBook 14',
        series: 'ZenBook Series',
        image: '/models/asus-zenbook.jpg',
        guides: 31,
        difficulty: 'Medium',
        popularity: 84,
        year: '2023'
      },
      {
        id: 'rog-zephyrus-g14',
        name: 'ROG Zephyrus G14',
        series: 'ROG Gaming',
        image: '/models/asus-rog.jpg',
        guides: 42,
        difficulty: 'Hard',
        popularity: 91,
        year: '2023'
      }
    ]
  }
};

const DIFFICULTY_COLORS: Record<string, string> = {
  'Easy': 'bg-green-100 text-green-700 border-green-200',
  'Medium': 'bg-amber-100 text-amber-700 border-amber-200',
  'Hard': 'bg-red-100 text-red-700 border-red-200'
};

export default function BrandModels() {
  const router = useRouter();
  const { brand } = router.query;
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('popularity');
  const [filteredModels, setFilteredModels] = useState<any[]>([]);

  const brandData = brand ? BRAND_DATA[brand as string] : null;

  useEffect(() => {
    if (brandData) {
      let models = [...brandData.models];

      // Filter by search
      if (searchQuery) {
        models = models.filter(model =>
          model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          model.series.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }

      // Sort
      if (sortBy === 'popularity') {
        models.sort((a, b) => b.popularity - a.popularity);
      } else if (sortBy === 'guides') {
        models.sort((a, b) => b.guides - a.guides);
      } else if (sortBy === 'year') {
        models.sort((a, b) => b.year.localeCompare(a.year));
      }

      setFilteredModels(models);
    }
  }, [brand, searchQuery, sortBy, brandData]);

  if (!brandData) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-neutral-600">Loading...</p>
        </div>
      </div>
    );
  }

  const handleModelClick = (modelId: string) => {
    router.push(`/guides/${brand}/${modelId}`);
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link 
            href="/guides"
            className="inline-flex items-center text-neutral-600 hover:text-neutral-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to all brands
          </Link>

          <div className="flex items-center gap-4 mb-4">
            <div 
              className="w-16 h-16 rounded-xl flex items-center justify-center text-3xl font-bold text-white"
              style={{ backgroundColor: brandData.color }}
            >
              {brandData.name.charAt(0)}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-neutral-900">
                {brandData.name} Repair Guides
              </h1>
              <p className="text-neutral-600 mt-1">
                {brandData.description}
              </p>
            </div>
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col md:flex-row gap-4 mt-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 w-5 h-5" />
              <Input
                type="text"
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e: any) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
            >
              <option value="popularity">Most Popular</option>
              <option value="guides">Most Guides</option>
              <option value="year">Newest First</option>
            </select>
          </div>
        </div>
      </div>

      {/* Models Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-6">
          <p className="text-neutral-600">
            {filteredModels.length} model{filteredModels.length !== 1 ? 's' : ''} found
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((model) => (
            <Card
              key={model.id}
              hover
              onClick={() => handleModelClick(model.id)}
              className="cursor-pointer group overflow-hidden"
            >
              {/* Model Image */}
              <div className="aspect-video bg-gradient-to-br from-neutral-100 to-neutral-200 flex items-center justify-center">
                <Laptop className="w-24 h-24 text-neutral-400 group-hover:text-neutral-600 transition-colors" />
              </div>

              <CardContent className="p-6">
                {/* Series Badge */}
                <Badge variant="default" className="mb-3">
                  {model.series}
                </Badge>

                {/* Model Name */}
                <h3 className="text-lg font-semibold text-neutral-900 mb-2 group-hover:text-blue-600 transition-colors">
                  {model.name}
                </h3>

                {/* Stats */}
                <div className="flex items-center gap-4 text-sm text-neutral-600 mb-4">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {model.year}
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-4 h-4" />
                    {model.popularity}% popular
                  </span>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-neutral-200">
                  <span className="text-sm font-medium text-neutral-900">
                    {model.guides} guides
                  </span>
                  <Badge 
                    variant="default"
                    className={DIFFICULTY_COLORS[model.difficulty]}
                  >
                    {model.difficulty}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredModels.length === 0 && (
          <div className="text-center py-12">
            <p className="text-neutral-600">No models found matching your search.</p>
          </div>
        )}
      </div>
    </div>
  );
}
