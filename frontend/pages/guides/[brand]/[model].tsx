import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Card, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Input } from '../../../components/ui/Input';
import { 
  ArrowLeft, 
  Search, 
  Clock, 
  Wrench, 
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Eye,
  Download
} from 'lucide-react';

// Mock guide data - will be replaced with API
const GUIDES_DATA: Record<string, any> = {
  'lenovo_ideapad-5': {
    modelName: 'IdeaPad 5',
    brandName: 'Lenovo',
    guides: {
      troubleshooting: [
        {
          id: 'battery-not-charging',
          title: 'Battery Not Charging',
          description: 'Fix battery charging issues and power management',
          difficulty: 'Easy',
          time: '15-30 min',
          tools: ['No tools required'],
          views: 12453,
          rating: 4.8,
          steps: 6
        },
        {
          id: 'no-boot',
          title: 'Laptop Won\'t Turn On',
          description: 'Diagnose and fix power-on issues',
          difficulty: 'Medium',
          time: '30-60 min',
          tools: ['Multimeter'],
          views: 8921,
          rating: 4.6,
          steps: 8
        }
      ],
      replacement: [
        {
          id: 'battery-replacement',
          title: 'Battery Replacement',
          description: 'Remove and replace the internal battery',
          difficulty: 'Easy',
          time: '10-20 min',
          tools: ['Phillips #0', 'Spudger'],
          views: 15632,
          rating: 4.9,
          steps: 4
        },
        {
          id: 'ssd-upgrade',
          title: 'SSD Upgrade',
          description: 'Upgrade or replace M.2 NVMe SSD',
          difficulty: 'Easy',
          time: '15-25 min',
          tools: ['Phillips #0'],
          views: 9847,
          rating: 4.7,
          steps: 5
        },
        {
          id: 'ram-upgrade',
          title: 'RAM Upgrade',
          description: 'Add or replace DDR4 memory modules',
          difficulty: 'Easy',
          time: '10-15 min',
          tools: ['Phillips #0'],
          views: 11234,
          rating: 4.8,
          steps: 4
        },
        {
          id: 'keyboard-replacement',
          title: 'Keyboard Replacement',
          description: 'Replace damaged or faulty keyboard',
          difficulty: 'Medium',
          time: '45-60 min',
          tools: ['Phillips #0', 'Spudger', 'Tweezers'],
          views: 6543,
          rating: 4.5,
          steps: 12
        }
      ],
      upgrade: [
        {
          id: 'thermal-paste',
          title: 'Thermal Paste Replacement',
          description: 'Improve cooling by reapplying thermal paste',
          difficulty: 'Medium',
          time: '30-45 min',
          tools: ['Phillips #0', 'Thermal paste', 'Isopropyl alcohol'],
          views: 7821,
          rating: 4.6,
          steps: 9
        }
      ]
    }
  }
};

const DIFFICULTY_COLORS: Record<string, string> = {
  'Easy': 'bg-green-100 text-green-700 border-green-200',
  'Medium': 'bg-amber-100 text-amber-700 border-amber-200',
  'Hard': 'bg-red-100 text-red-700 border-red-200'
};

const CATEGORY_INFO: Record<string, any> = {
  troubleshooting: {
    title: 'Troubleshooting',
    icon: AlertTriangle,
    color: 'text-amber-600',
    description: 'Diagnose and fix common issues'
  },
  replacement: {
    title: 'Replacement Guides',
    icon: Wrench,
    color: 'text-blue-600',
    description: 'Replace damaged or worn components'
  },
  upgrade: {
    title: 'Upgrade Guides',
    icon: TrendingUp,
    color: 'text-purple-600',
    description: 'Enhance performance and capabilities'
  }
};

export default function ModelGuides() {
  const router = useRouter();
  const { brand, model } = router.query;
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const guideKey = `${brand}_${model}`;
  const guideData = GUIDES_DATA[guideKey];

  if (!guideData) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-neutral-600">Loading guides...</p>
        </div>
      </div>
    );
  }

  const handleGuideClick = (guideId: string) => {
    router.push(`/guides/${brand}/${model}/${guideId}`);
  };

  const filterGuides = (guides: any[]) => {
    if (!searchQuery) return guides;
    return guides.filter(guide =>
      guide.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      guide.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const renderGuideCard = (guide: any) => {
    const Icon = CheckCircle;
    
    return (
      <Card
        key={guide.id}
        hover
        onClick={() => handleGuideClick(guide.id)}
        className="cursor-pointer group"
      >
        <CardContent className="p-6">
          {/* Title and Difficulty */}
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-lg font-semibold text-neutral-900 group-hover:text-blue-600 transition-colors flex-1">
              {guide.title}
            </h3>
            <Badge className={`ml-3 ${DIFFICULTY_COLORS[guide.difficulty]}`}>
              {guide.difficulty}
            </Badge>
          </div>

          {/* Description */}
          <p className="text-neutral-600 text-sm mb-4">
            {guide.description}
          </p>

          {/* Stats Row */}
          <div className="flex items-center gap-4 text-sm text-neutral-600 mb-4">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {guide.time}
            </span>
            <span className="flex items-center gap-1">
              <Icon className="w-4 h-4" />
              {guide.steps} steps
            </span>
            <span className="flex items-center gap-1">
              <Eye className="w-4 h-4" />
              {guide.views.toLocaleString()}
            </span>
          </div>

          {/* Tools */}
          <div className="mb-4">
            <p className="text-xs font-medium text-neutral-500 mb-2">TOOLS REQUIRED</p>
            <div className="flex flex-wrap gap-2">
              {guide.tools.map((tool: string, idx: number) => (
                <span 
                  key={idx}
                  className="text-xs px-2 py-1 bg-neutral-100 text-neutral-700 rounded"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>

          {/* Rating */}
          <div className="flex items-center gap-2 pt-4 border-t border-neutral-200">
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <svg
                  key={i}
                  className={`w-4 h-4 ${
                    i < Math.floor(guide.rating)
                      ? 'text-yellow-400 fill-current'
                      : 'text-neutral-300'
                  }`}
                  viewBox="0 0 20 20"
                >
                  <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                </svg>
              ))}
            </div>
            <span className="text-sm text-neutral-600">
              {guide.rating.toFixed(1)}
            </span>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link 
            href={`/guides/${brand}`}
            className="inline-flex items-center text-neutral-600 hover:text-neutral-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to {guideData.brandName} models
          </Link>

          <h1 className="text-3xl font-bold text-neutral-900 mb-2">
            {guideData.brandName} {guideData.modelName}
          </h1>
          <p className="text-neutral-600">
            Complete repair and upgrade guides for your device
          </p>

          {/* Search */}
          <div className="mt-6 max-w-xl">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 w-5 h-5" />
              <Input
                type="text"
                placeholder="Search guides..."
                value={searchQuery}
                onChange={(e: any) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Category Navigation */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-6 overflow-x-auto">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`py-4 px-2 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                selectedCategory === null
                  ? 'border-neutral-900 text-neutral-900'
                  : 'border-transparent text-neutral-600 hover:text-neutral-900'
              }`}
            >
              All Guides
            </button>
            {Object.entries(CATEGORY_INFO).map(([key, info]) => {
              const categoryGuides = guideData.guides[key] || [];
              return (
                <button
                  key={key}
                  onClick={() => setSelectedCategory(key)}
                  className={`py-4 px-2 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                    selectedCategory === key
                      ? 'border-neutral-900 text-neutral-900'
                      : 'border-transparent text-neutral-600 hover:text-neutral-900'
                  }`}
                >
                  {info.title} ({categoryGuides.length})
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Guides Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {selectedCategory === null ? (
          // All categories
          Object.entries(CATEGORY_INFO).map(([categoryKey, categoryInfo]) => {
            const guides = filterGuides(guideData.guides[categoryKey] || []);
            if (guides.length === 0) return null;

            const CategoryIcon = categoryInfo.icon;

            return (
              <div key={categoryKey} className="mb-12">
                <div className="flex items-center gap-3 mb-6">
                  <CategoryIcon className={`w-6 h-6 ${categoryInfo.color}`} />
                  <h2 className="text-2xl font-bold text-neutral-900">
                    {categoryInfo.title}
                  </h2>
                  <span className="text-neutral-500">
                    ({guides.length})
                  </span>
                </div>
                <p className="text-neutral-600 mb-6">
                  {categoryInfo.description}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {guides.map(renderGuideCard)}
                </div>
              </div>
            );
          })
        ) : (
          // Single category
          (() => {
            const guides = filterGuides(guideData.guides[selectedCategory] || []);
            const categoryInfo = CATEGORY_INFO[selectedCategory];
            const CategoryIcon = categoryInfo.icon;

            return (
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <CategoryIcon className={`w-6 h-6 ${categoryInfo.color}`} />
                  <h2 className="text-2xl font-bold text-neutral-900">
                    {categoryInfo.title}
                  </h2>
                  <span className="text-neutral-500">
                    ({guides.length})
                  </span>
                </div>
                <p className="text-neutral-600 mb-6">
                  {categoryInfo.description}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {guides.length > 0 ? (
                    guides.map(renderGuideCard)
                  ) : (
                    <p className="text-neutral-600 col-span-2">
                      No guides found matching your search.
                    </p>
                  )}
                </div>
              </div>
            );
          })()
        )}
      </div>
    </div>
  );
}
