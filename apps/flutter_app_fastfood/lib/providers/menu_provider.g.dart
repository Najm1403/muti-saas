// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'menu_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$categoriesHash() => r'50722e7914ed43f9f5bb2a98847837b36e615566';

/// All categories from the local catalog, ordered by display_order.
///
/// Refetch by invalidating this provider after a sync completes.
///
/// Copied from [categories].
@ProviderFor(categories)
final categoriesProvider =
    AutoDisposeFutureProvider<List<CategoriesTableData>>.internal(
  categories,
  name: r'categoriesProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$categoriesHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CategoriesRef = AutoDisposeFutureProviderRef<List<CategoriesTableData>>;
String _$productsByCategoryHash() =>
    r'd079da7511dc646fc4fe808e66a066f570f241f9';

/// Copied from Dart SDK
class _SystemHash {
  _SystemHash._();

  static int combine(int hash, int value) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + value);
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x0007ffff & hash) << 10));
    return hash ^ (hash >> 6);
  }

  static int finish(int hash) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x03ffffff & hash) << 3));
    // ignore: parameter_assignments
    hash = hash ^ (hash >> 11);
    return 0x1fffffff & (hash + ((0x00003fff & hash) << 15));
  }
}

/// Active products in [categoryId], ordered by display_order.
///
/// The family key is the category UUID. Invalidate the whole family after sync.
///
/// Copied from [productsByCategory].
@ProviderFor(productsByCategory)
const productsByCategoryProvider = ProductsByCategoryFamily();

/// Active products in [categoryId], ordered by display_order.
///
/// The family key is the category UUID. Invalidate the whole family after sync.
///
/// Copied from [productsByCategory].
class ProductsByCategoryFamily
    extends Family<AsyncValue<List<ProductsTableData>>> {
  /// Active products in [categoryId], ordered by display_order.
  ///
  /// The family key is the category UUID. Invalidate the whole family after sync.
  ///
  /// Copied from [productsByCategory].
  const ProductsByCategoryFamily();

  /// Active products in [categoryId], ordered by display_order.
  ///
  /// The family key is the category UUID. Invalidate the whole family after sync.
  ///
  /// Copied from [productsByCategory].
  ProductsByCategoryProvider call(
    String categoryId,
  ) {
    return ProductsByCategoryProvider(
      categoryId,
    );
  }

  @override
  ProductsByCategoryProvider getProviderOverride(
    covariant ProductsByCategoryProvider provider,
  ) {
    return call(
      provider.categoryId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'productsByCategoryProvider';
}

/// Active products in [categoryId], ordered by display_order.
///
/// The family key is the category UUID. Invalidate the whole family after sync.
///
/// Copied from [productsByCategory].
class ProductsByCategoryProvider
    extends AutoDisposeFutureProvider<List<ProductsTableData>> {
  /// Active products in [categoryId], ordered by display_order.
  ///
  /// The family key is the category UUID. Invalidate the whole family after sync.
  ///
  /// Copied from [productsByCategory].
  ProductsByCategoryProvider(
    String categoryId,
  ) : this._internal(
          (ref) => productsByCategory(
            ref as ProductsByCategoryRef,
            categoryId,
          ),
          from: productsByCategoryProvider,
          name: r'productsByCategoryProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$productsByCategoryHash,
          dependencies: ProductsByCategoryFamily._dependencies,
          allTransitiveDependencies:
              ProductsByCategoryFamily._allTransitiveDependencies,
          categoryId: categoryId,
        );

  ProductsByCategoryProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.categoryId,
  }) : super.internal();

  final String categoryId;

  @override
  Override overrideWith(
    FutureOr<List<ProductsTableData>> Function(ProductsByCategoryRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: ProductsByCategoryProvider._internal(
        (ref) => create(ref as ProductsByCategoryRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        categoryId: categoryId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<List<ProductsTableData>> createElement() {
    return _ProductsByCategoryProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is ProductsByCategoryProvider &&
        other.categoryId == categoryId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, categoryId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin ProductsByCategoryRef
    on AutoDisposeFutureProviderRef<List<ProductsTableData>> {
  /// The parameter `categoryId` of this provider.
  String get categoryId;
}

class _ProductsByCategoryProviderElement
    extends AutoDisposeFutureProviderElement<List<ProductsTableData>>
    with ProductsByCategoryRef {
  _ProductsByCategoryProviderElement(super.provider);

  @override
  String get categoryId => (origin as ProductsByCategoryProvider).categoryId;
}

String _$allActiveProductsHash() => r'4de1f06c1fdaabb9ed1bb25f74494e2a42e1ecff';

/// Active products across every category.
///
/// Used for search/lookup screens where a flat product list is needed.
///
/// Copied from [allActiveProducts].
@ProviderFor(allActiveProducts)
final allActiveProductsProvider =
    AutoDisposeFutureProvider<List<ProductsTableData>>.internal(
  allActiveProducts,
  name: r'allActiveProductsProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$allActiveProductsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AllActiveProductsRef
    = AutoDisposeFutureProviderRef<List<ProductsTableData>>;
String _$searchProductsHash() => r'05832241e78c6de5c98a9b8d52403e0f957bb0c9';

/// Active products matching a free-text [query] (name / product code /
/// attached Variant Selection group or option name), spanning every
/// category. The family key is the trimmed, lower-cased search text.
///
/// Copied from [searchProducts].
@ProviderFor(searchProducts)
const searchProductsProvider = SearchProductsFamily();

/// Active products matching a free-text [query] (name / product code /
/// attached Variant Selection group or option name), spanning every
/// category. The family key is the trimmed, lower-cased search text.
///
/// Copied from [searchProducts].
class SearchProductsFamily extends Family<AsyncValue<List<ProductsTableData>>> {
  /// Active products matching a free-text [query] (name / product code /
  /// attached Variant Selection group or option name), spanning every
  /// category. The family key is the trimmed, lower-cased search text.
  ///
  /// Copied from [searchProducts].
  const SearchProductsFamily();

  /// Active products matching a free-text [query] (name / product code /
  /// attached Variant Selection group or option name), spanning every
  /// category. The family key is the trimmed, lower-cased search text.
  ///
  /// Copied from [searchProducts].
  SearchProductsProvider call(
    String query,
  ) {
    return SearchProductsProvider(
      query,
    );
  }

  @override
  SearchProductsProvider getProviderOverride(
    covariant SearchProductsProvider provider,
  ) {
    return call(
      provider.query,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'searchProductsProvider';
}

/// Active products matching a free-text [query] (name / product code /
/// attached Variant Selection group or option name), spanning every
/// category. The family key is the trimmed, lower-cased search text.
///
/// Copied from [searchProducts].
class SearchProductsProvider
    extends AutoDisposeFutureProvider<List<ProductsTableData>> {
  /// Active products matching a free-text [query] (name / product code /
  /// attached Variant Selection group or option name), spanning every
  /// category. The family key is the trimmed, lower-cased search text.
  ///
  /// Copied from [searchProducts].
  SearchProductsProvider(
    String query,
  ) : this._internal(
          (ref) => searchProducts(
            ref as SearchProductsRef,
            query,
          ),
          from: searchProductsProvider,
          name: r'searchProductsProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$searchProductsHash,
          dependencies: SearchProductsFamily._dependencies,
          allTransitiveDependencies:
              SearchProductsFamily._allTransitiveDependencies,
          query: query,
        );

  SearchProductsProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.query,
  }) : super.internal();

  final String query;

  @override
  Override overrideWith(
    FutureOr<List<ProductsTableData>> Function(SearchProductsRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: SearchProductsProvider._internal(
        (ref) => create(ref as SearchProductsRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        query: query,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<List<ProductsTableData>> createElement() {
    return _SearchProductsProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is SearchProductsProvider && other.query == query;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, query.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin SearchProductsRef
    on AutoDisposeFutureProviderRef<List<ProductsTableData>> {
  /// The parameter `query` of this provider.
  String get query;
}

class _SearchProductsProviderElement
    extends AutoDisposeFutureProviderElement<List<ProductsTableData>>
    with SearchProductsRef {
  _SearchProductsProviderElement(super.provider);

  @override
  String get query => (origin as SearchProductsProvider).query;
}

String _$componentDisplayNameHash() =>
    r'7815f253e6c46afdf73c1ecd017252173eac3001';

/// A standalone inventory component's qualified picker name (`RAM: 4 GB`).
///
/// Copied from [componentDisplayName].
@ProviderFor(componentDisplayName)
const componentDisplayNameProvider = ComponentDisplayNameFamily();

/// A standalone inventory component's qualified picker name (`RAM: 4 GB`).
///
/// Copied from [componentDisplayName].
class ComponentDisplayNameFamily extends Family<AsyncValue<String?>> {
  /// A standalone inventory component's qualified picker name (`RAM: 4 GB`).
  ///
  /// Copied from [componentDisplayName].
  const ComponentDisplayNameFamily();

  /// A standalone inventory component's qualified picker name (`RAM: 4 GB`).
  ///
  /// Copied from [componentDisplayName].
  ComponentDisplayNameProvider call(
    String productId,
  ) {
    return ComponentDisplayNameProvider(
      productId,
    );
  }

  @override
  ComponentDisplayNameProvider getProviderOverride(
    covariant ComponentDisplayNameProvider provider,
  ) {
    return call(
      provider.productId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'componentDisplayNameProvider';
}

/// A standalone inventory component's qualified picker name (`RAM: 4 GB`).
///
/// Copied from [componentDisplayName].
class ComponentDisplayNameProvider extends AutoDisposeFutureProvider<String?> {
  /// A standalone inventory component's qualified picker name (`RAM: 4 GB`).
  ///
  /// Copied from [componentDisplayName].
  ComponentDisplayNameProvider(
    String productId,
  ) : this._internal(
          (ref) => componentDisplayName(
            ref as ComponentDisplayNameRef,
            productId,
          ),
          from: componentDisplayNameProvider,
          name: r'componentDisplayNameProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$componentDisplayNameHash,
          dependencies: ComponentDisplayNameFamily._dependencies,
          allTransitiveDependencies:
              ComponentDisplayNameFamily._allTransitiveDependencies,
          productId: productId,
        );

  ComponentDisplayNameProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.productId,
  }) : super.internal();

  final String productId;

  @override
  Override overrideWith(
    FutureOr<String?> Function(ComponentDisplayNameRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: ComponentDisplayNameProvider._internal(
        (ref) => create(ref as ComponentDisplayNameRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        productId: productId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<String?> createElement() {
    return _ComponentDisplayNameProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is ComponentDisplayNameProvider &&
        other.productId == productId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, productId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin ComponentDisplayNameRef on AutoDisposeFutureProviderRef<String?> {
  /// The parameter `productId` of this provider.
  String get productId;
}

class _ComponentDisplayNameProviderElement
    extends AutoDisposeFutureProviderElement<String?>
    with ComponentDisplayNameRef {
  _ComponentDisplayNameProviderElement(super.provider);

  @override
  String get productId => (origin as ComponentDisplayNameProvider).productId;
}

String _$variantOptionGroupsHash() =>
    r'8669092e1245683fb305cb29ae6ca7cdf203cbf4';

/// Variant Option Groups attached to [productId], ordered by display_order.
///
/// Structurally separate from [addonGroupsProvider] — never feeds into
/// variant generation (spec A1/D4).
///
/// Copied from [variantOptionGroups].
@ProviderFor(variantOptionGroups)
const variantOptionGroupsProvider = VariantOptionGroupsFamily();

/// Variant Option Groups attached to [productId], ordered by display_order.
///
/// Structurally separate from [addonGroupsProvider] — never feeds into
/// variant generation (spec A1/D4).
///
/// Copied from [variantOptionGroups].
class VariantOptionGroupsFamily
    extends Family<AsyncValue<List<VariantOptionGroupsTableData>>> {
  /// Variant Option Groups attached to [productId], ordered by display_order.
  ///
  /// Structurally separate from [addonGroupsProvider] — never feeds into
  /// variant generation (spec A1/D4).
  ///
  /// Copied from [variantOptionGroups].
  const VariantOptionGroupsFamily();

  /// Variant Option Groups attached to [productId], ordered by display_order.
  ///
  /// Structurally separate from [addonGroupsProvider] — never feeds into
  /// variant generation (spec A1/D4).
  ///
  /// Copied from [variantOptionGroups].
  VariantOptionGroupsProvider call(
    String productId,
  ) {
    return VariantOptionGroupsProvider(
      productId,
    );
  }

  @override
  VariantOptionGroupsProvider getProviderOverride(
    covariant VariantOptionGroupsProvider provider,
  ) {
    return call(
      provider.productId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'variantOptionGroupsProvider';
}

/// Variant Option Groups attached to [productId], ordered by display_order.
///
/// Structurally separate from [addonGroupsProvider] — never feeds into
/// variant generation (spec A1/D4).
///
/// Copied from [variantOptionGroups].
class VariantOptionGroupsProvider
    extends AutoDisposeFutureProvider<List<VariantOptionGroupsTableData>> {
  /// Variant Option Groups attached to [productId], ordered by display_order.
  ///
  /// Structurally separate from [addonGroupsProvider] — never feeds into
  /// variant generation (spec A1/D4).
  ///
  /// Copied from [variantOptionGroups].
  VariantOptionGroupsProvider(
    String productId,
  ) : this._internal(
          (ref) => variantOptionGroups(
            ref as VariantOptionGroupsRef,
            productId,
          ),
          from: variantOptionGroupsProvider,
          name: r'variantOptionGroupsProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$variantOptionGroupsHash,
          dependencies: VariantOptionGroupsFamily._dependencies,
          allTransitiveDependencies:
              VariantOptionGroupsFamily._allTransitiveDependencies,
          productId: productId,
        );

  VariantOptionGroupsProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.productId,
  }) : super.internal();

  final String productId;

  @override
  Override overrideWith(
    FutureOr<List<VariantOptionGroupsTableData>> Function(
            VariantOptionGroupsRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: VariantOptionGroupsProvider._internal(
        (ref) => create(ref as VariantOptionGroupsRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        productId: productId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<List<VariantOptionGroupsTableData>>
      createElement() {
    return _VariantOptionGroupsProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is VariantOptionGroupsProvider && other.productId == productId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, productId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin VariantOptionGroupsRef
    on AutoDisposeFutureProviderRef<List<VariantOptionGroupsTableData>> {
  /// The parameter `productId` of this provider.
  String get productId;
}

class _VariantOptionGroupsProviderElement
    extends AutoDisposeFutureProviderElement<List<VariantOptionGroupsTableData>>
    with VariantOptionGroupsRef {
  _VariantOptionGroupsProviderElement(super.provider);

  @override
  String get productId => (origin as VariantOptionGroupsProvider).productId;
}

String _$variantOptionsForGroupHash() =>
    r'308e5de72f916ec4711b4b2f3df528b06f1452b8';

/// Active Variant Options inside [groupId], ordered by display_order.
///
/// Copied from [variantOptionsForGroup].
@ProviderFor(variantOptionsForGroup)
const variantOptionsForGroupProvider = VariantOptionsForGroupFamily();

/// Active Variant Options inside [groupId], ordered by display_order.
///
/// Copied from [variantOptionsForGroup].
class VariantOptionsForGroupFamily
    extends Family<AsyncValue<List<VariantOptionsTableData>>> {
  /// Active Variant Options inside [groupId], ordered by display_order.
  ///
  /// Copied from [variantOptionsForGroup].
  const VariantOptionsForGroupFamily();

  /// Active Variant Options inside [groupId], ordered by display_order.
  ///
  /// Copied from [variantOptionsForGroup].
  VariantOptionsForGroupProvider call(
    String groupId,
  ) {
    return VariantOptionsForGroupProvider(
      groupId,
    );
  }

  @override
  VariantOptionsForGroupProvider getProviderOverride(
    covariant VariantOptionsForGroupProvider provider,
  ) {
    return call(
      provider.groupId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'variantOptionsForGroupProvider';
}

/// Active Variant Options inside [groupId], ordered by display_order.
///
/// Copied from [variantOptionsForGroup].
class VariantOptionsForGroupProvider
    extends AutoDisposeFutureProvider<List<VariantOptionsTableData>> {
  /// Active Variant Options inside [groupId], ordered by display_order.
  ///
  /// Copied from [variantOptionsForGroup].
  VariantOptionsForGroupProvider(
    String groupId,
  ) : this._internal(
          (ref) => variantOptionsForGroup(
            ref as VariantOptionsForGroupRef,
            groupId,
          ),
          from: variantOptionsForGroupProvider,
          name: r'variantOptionsForGroupProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$variantOptionsForGroupHash,
          dependencies: VariantOptionsForGroupFamily._dependencies,
          allTransitiveDependencies:
              VariantOptionsForGroupFamily._allTransitiveDependencies,
          groupId: groupId,
        );

  VariantOptionsForGroupProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.groupId,
  }) : super.internal();

  final String groupId;

  @override
  Override overrideWith(
    FutureOr<List<VariantOptionsTableData>> Function(
            VariantOptionsForGroupRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: VariantOptionsForGroupProvider._internal(
        (ref) => create(ref as VariantOptionsForGroupRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        groupId: groupId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<List<VariantOptionsTableData>>
      createElement() {
    return _VariantOptionsForGroupProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is VariantOptionsForGroupProvider && other.groupId == groupId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, groupId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin VariantOptionsForGroupRef
    on AutoDisposeFutureProviderRef<List<VariantOptionsTableData>> {
  /// The parameter `groupId` of this provider.
  String get groupId;
}

class _VariantOptionsForGroupProviderElement
    extends AutoDisposeFutureProviderElement<List<VariantOptionsTableData>>
    with VariantOptionsForGroupRef {
  _VariantOptionsForGroupProviderElement(super.provider);

  @override
  String get groupId => (origin as VariantOptionsForGroupProvider).groupId;
}

String _$variantsForProductHash() =>
    r'ac898bef483cd777fc9a863482c549b71b1414ce';

/// Every synced composed Variant for [productId] — the real, sellable SKUs.
///
/// A product with no attached Variant Option Groups still has exactly one
/// (the zero-option default) row here.
///
/// Copied from [variantsForProduct].
@ProviderFor(variantsForProduct)
const variantsForProductProvider = VariantsForProductFamily();

/// Every synced composed Variant for [productId] — the real, sellable SKUs.
///
/// A product with no attached Variant Option Groups still has exactly one
/// (the zero-option default) row here.
///
/// Copied from [variantsForProduct].
class VariantsForProductFamily
    extends Family<AsyncValue<List<VariantsTableData>>> {
  /// Every synced composed Variant for [productId] — the real, sellable SKUs.
  ///
  /// A product with no attached Variant Option Groups still has exactly one
  /// (the zero-option default) row here.
  ///
  /// Copied from [variantsForProduct].
  const VariantsForProductFamily();

  /// Every synced composed Variant for [productId] — the real, sellable SKUs.
  ///
  /// A product with no attached Variant Option Groups still has exactly one
  /// (the zero-option default) row here.
  ///
  /// Copied from [variantsForProduct].
  VariantsForProductProvider call(
    String productId,
  ) {
    return VariantsForProductProvider(
      productId,
    );
  }

  @override
  VariantsForProductProvider getProviderOverride(
    covariant VariantsForProductProvider provider,
  ) {
    return call(
      provider.productId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'variantsForProductProvider';
}

/// Every synced composed Variant for [productId] — the real, sellable SKUs.
///
/// A product with no attached Variant Option Groups still has exactly one
/// (the zero-option default) row here.
///
/// Copied from [variantsForProduct].
class VariantsForProductProvider
    extends AutoDisposeFutureProvider<List<VariantsTableData>> {
  /// Every synced composed Variant for [productId] — the real, sellable SKUs.
  ///
  /// A product with no attached Variant Option Groups still has exactly one
  /// (the zero-option default) row here.
  ///
  /// Copied from [variantsForProduct].
  VariantsForProductProvider(
    String productId,
  ) : this._internal(
          (ref) => variantsForProduct(
            ref as VariantsForProductRef,
            productId,
          ),
          from: variantsForProductProvider,
          name: r'variantsForProductProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$variantsForProductHash,
          dependencies: VariantsForProductFamily._dependencies,
          allTransitiveDependencies:
              VariantsForProductFamily._allTransitiveDependencies,
          productId: productId,
        );

  VariantsForProductProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.productId,
  }) : super.internal();

  final String productId;

  @override
  Override overrideWith(
    FutureOr<List<VariantsTableData>> Function(VariantsForProductRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: VariantsForProductProvider._internal(
        (ref) => create(ref as VariantsForProductRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        productId: productId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<List<VariantsTableData>> createElement() {
    return _VariantsForProductProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is VariantsForProductProvider && other.productId == productId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, productId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin VariantsForProductRef
    on AutoDisposeFutureProviderRef<List<VariantsTableData>> {
  /// The parameter `productId` of this provider.
  String get productId;
}

class _VariantsForProductProviderElement
    extends AutoDisposeFutureProviderElement<List<VariantsTableData>>
    with VariantsForProductRef {
  _VariantsForProductProviderElement(super.provider);

  @override
  String get productId => (origin as VariantsForProductProvider).productId;
}

String _$variantByIdHash() => r'746a3c7c6c50c3c4a4efcde599d6cebb37a07975';

/// The single Variant row for [variantId] — used to price/resolve a
/// selected Inventory Component (Laptop Store shareable-inventory model),
/// which belongs to a different product than the one currently open in the
/// picker, so it isn't already present in [variantsForProduct].
///
/// Copied from [variantById].
@ProviderFor(variantById)
const variantByIdProvider = VariantByIdFamily();

/// The single Variant row for [variantId] — used to price/resolve a
/// selected Inventory Component (Laptop Store shareable-inventory model),
/// which belongs to a different product than the one currently open in the
/// picker, so it isn't already present in [variantsForProduct].
///
/// Copied from [variantById].
class VariantByIdFamily extends Family<AsyncValue<VariantsTableData?>> {
  /// The single Variant row for [variantId] — used to price/resolve a
  /// selected Inventory Component (Laptop Store shareable-inventory model),
  /// which belongs to a different product than the one currently open in the
  /// picker, so it isn't already present in [variantsForProduct].
  ///
  /// Copied from [variantById].
  const VariantByIdFamily();

  /// The single Variant row for [variantId] — used to price/resolve a
  /// selected Inventory Component (Laptop Store shareable-inventory model),
  /// which belongs to a different product than the one currently open in the
  /// picker, so it isn't already present in [variantsForProduct].
  ///
  /// Copied from [variantById].
  VariantByIdProvider call(
    String variantId,
  ) {
    return VariantByIdProvider(
      variantId,
    );
  }

  @override
  VariantByIdProvider getProviderOverride(
    covariant VariantByIdProvider provider,
  ) {
    return call(
      provider.variantId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'variantByIdProvider';
}

/// The single Variant row for [variantId] — used to price/resolve a
/// selected Inventory Component (Laptop Store shareable-inventory model),
/// which belongs to a different product than the one currently open in the
/// picker, so it isn't already present in [variantsForProduct].
///
/// Copied from [variantById].
class VariantByIdProvider
    extends AutoDisposeFutureProvider<VariantsTableData?> {
  /// The single Variant row for [variantId] — used to price/resolve a
  /// selected Inventory Component (Laptop Store shareable-inventory model),
  /// which belongs to a different product than the one currently open in the
  /// picker, so it isn't already present in [variantsForProduct].
  ///
  /// Copied from [variantById].
  VariantByIdProvider(
    String variantId,
  ) : this._internal(
          (ref) => variantById(
            ref as VariantByIdRef,
            variantId,
          ),
          from: variantByIdProvider,
          name: r'variantByIdProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$variantByIdHash,
          dependencies: VariantByIdFamily._dependencies,
          allTransitiveDependencies:
              VariantByIdFamily._allTransitiveDependencies,
          variantId: variantId,
        );

  VariantByIdProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.variantId,
  }) : super.internal();

  final String variantId;

  @override
  Override overrideWith(
    FutureOr<VariantsTableData?> Function(VariantByIdRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: VariantByIdProvider._internal(
        (ref) => create(ref as VariantByIdRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        variantId: variantId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<VariantsTableData?> createElement() {
    return _VariantByIdProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is VariantByIdProvider && other.variantId == variantId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, variantId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin VariantByIdRef on AutoDisposeFutureProviderRef<VariantsTableData?> {
  /// The parameter `variantId` of this provider.
  String get variantId;
}

class _VariantByIdProviderElement
    extends AutoDisposeFutureProviderElement<VariantsTableData?>
    with VariantByIdRef {
  _VariantByIdProviderElement(super.provider);

  @override
  String get variantId => (origin as VariantByIdProvider).variantId;
}

String _$branchStockForVariantHash() =>
    r'1f931f4488826fdcdaa78faadd30aabe447e7fb1';

/// This device's branch stock row for [variantId], or null when untracked.
///
/// Copied from [branchStockForVariant].
@ProviderFor(branchStockForVariant)
const branchStockForVariantProvider = BranchStockForVariantFamily();

/// This device's branch stock row for [variantId], or null when untracked.
///
/// Copied from [branchStockForVariant].
class BranchStockForVariantFamily
    extends Family<AsyncValue<VariantBranchStockTableData?>> {
  /// This device's branch stock row for [variantId], or null when untracked.
  ///
  /// Copied from [branchStockForVariant].
  const BranchStockForVariantFamily();

  /// This device's branch stock row for [variantId], or null when untracked.
  ///
  /// Copied from [branchStockForVariant].
  BranchStockForVariantProvider call(
    String variantId,
  ) {
    return BranchStockForVariantProvider(
      variantId,
    );
  }

  @override
  BranchStockForVariantProvider getProviderOverride(
    covariant BranchStockForVariantProvider provider,
  ) {
    return call(
      provider.variantId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'branchStockForVariantProvider';
}

/// This device's branch stock row for [variantId], or null when untracked.
///
/// Copied from [branchStockForVariant].
class BranchStockForVariantProvider
    extends AutoDisposeFutureProvider<VariantBranchStockTableData?> {
  /// This device's branch stock row for [variantId], or null when untracked.
  ///
  /// Copied from [branchStockForVariant].
  BranchStockForVariantProvider(
    String variantId,
  ) : this._internal(
          (ref) => branchStockForVariant(
            ref as BranchStockForVariantRef,
            variantId,
          ),
          from: branchStockForVariantProvider,
          name: r'branchStockForVariantProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$branchStockForVariantHash,
          dependencies: BranchStockForVariantFamily._dependencies,
          allTransitiveDependencies:
              BranchStockForVariantFamily._allTransitiveDependencies,
          variantId: variantId,
        );

  BranchStockForVariantProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.variantId,
  }) : super.internal();

  final String variantId;

  @override
  Override overrideWith(
    FutureOr<VariantBranchStockTableData?> Function(
            BranchStockForVariantRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: BranchStockForVariantProvider._internal(
        (ref) => create(ref as BranchStockForVariantRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        variantId: variantId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<VariantBranchStockTableData?>
      createElement() {
    return _BranchStockForVariantProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is BranchStockForVariantProvider &&
        other.variantId == variantId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, variantId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin BranchStockForVariantRef
    on AutoDisposeFutureProviderRef<VariantBranchStockTableData?> {
  /// The parameter `variantId` of this provider.
  String get variantId;
}

class _BranchStockForVariantProviderElement
    extends AutoDisposeFutureProviderElement<VariantBranchStockTableData?>
    with BranchStockForVariantRef {
  _BranchStockForVariantProviderElement(super.provider);

  @override
  String get variantId => (origin as BranchStockForVariantProvider).variantId;
}

String _$addonGroupsHash() => r'88a828c58442544cdf92df1cd1f5a6735fb3aa5a';

/// Add-on Groups attached to [productId], ordered by display_order.
///
/// Copied from [addonGroups].
@ProviderFor(addonGroups)
const addonGroupsProvider = AddonGroupsFamily();

/// Add-on Groups attached to [productId], ordered by display_order.
///
/// Copied from [addonGroups].
class AddonGroupsFamily extends Family<AsyncValue<List<AddonGroupsTableData>>> {
  /// Add-on Groups attached to [productId], ordered by display_order.
  ///
  /// Copied from [addonGroups].
  const AddonGroupsFamily();

  /// Add-on Groups attached to [productId], ordered by display_order.
  ///
  /// Copied from [addonGroups].
  AddonGroupsProvider call(
    String productId,
  ) {
    return AddonGroupsProvider(
      productId,
    );
  }

  @override
  AddonGroupsProvider getProviderOverride(
    covariant AddonGroupsProvider provider,
  ) {
    return call(
      provider.productId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'addonGroupsProvider';
}

/// Add-on Groups attached to [productId], ordered by display_order.
///
/// Copied from [addonGroups].
class AddonGroupsProvider
    extends AutoDisposeFutureProvider<List<AddonGroupsTableData>> {
  /// Add-on Groups attached to [productId], ordered by display_order.
  ///
  /// Copied from [addonGroups].
  AddonGroupsProvider(
    String productId,
  ) : this._internal(
          (ref) => addonGroups(
            ref as AddonGroupsRef,
            productId,
          ),
          from: addonGroupsProvider,
          name: r'addonGroupsProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$addonGroupsHash,
          dependencies: AddonGroupsFamily._dependencies,
          allTransitiveDependencies:
              AddonGroupsFamily._allTransitiveDependencies,
          productId: productId,
        );

  AddonGroupsProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.productId,
  }) : super.internal();

  final String productId;

  @override
  Override overrideWith(
    FutureOr<List<AddonGroupsTableData>> Function(AddonGroupsRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: AddonGroupsProvider._internal(
        (ref) => create(ref as AddonGroupsRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        productId: productId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<List<AddonGroupsTableData>> createElement() {
    return _AddonGroupsProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is AddonGroupsProvider && other.productId == productId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, productId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin AddonGroupsRef
    on AutoDisposeFutureProviderRef<List<AddonGroupsTableData>> {
  /// The parameter `productId` of this provider.
  String get productId;
}

class _AddonGroupsProviderElement
    extends AutoDisposeFutureProviderElement<List<AddonGroupsTableData>>
    with AddonGroupsRef {
  _AddonGroupsProviderElement(super.provider);

  @override
  String get productId => (origin as AddonGroupsProvider).productId;
}

String _$addonItemsForGroupHash() =>
    r'df0f121ec5079a5c45fc9c1a5f4eff24b9907d8b';

/// Active Add-on Items inside [groupId], ordered by display_order.
///
/// Copied from [addonItemsForGroup].
@ProviderFor(addonItemsForGroup)
const addonItemsForGroupProvider = AddonItemsForGroupFamily();

/// Active Add-on Items inside [groupId], ordered by display_order.
///
/// Copied from [addonItemsForGroup].
class AddonItemsForGroupFamily
    extends Family<AsyncValue<List<AddonItemsTableData>>> {
  /// Active Add-on Items inside [groupId], ordered by display_order.
  ///
  /// Copied from [addonItemsForGroup].
  const AddonItemsForGroupFamily();

  /// Active Add-on Items inside [groupId], ordered by display_order.
  ///
  /// Copied from [addonItemsForGroup].
  AddonItemsForGroupProvider call(
    String groupId,
  ) {
    return AddonItemsForGroupProvider(
      groupId,
    );
  }

  @override
  AddonItemsForGroupProvider getProviderOverride(
    covariant AddonItemsForGroupProvider provider,
  ) {
    return call(
      provider.groupId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'addonItemsForGroupProvider';
}

/// Active Add-on Items inside [groupId], ordered by display_order.
///
/// Copied from [addonItemsForGroup].
class AddonItemsForGroupProvider
    extends AutoDisposeFutureProvider<List<AddonItemsTableData>> {
  /// Active Add-on Items inside [groupId], ordered by display_order.
  ///
  /// Copied from [addonItemsForGroup].
  AddonItemsForGroupProvider(
    String groupId,
  ) : this._internal(
          (ref) => addonItemsForGroup(
            ref as AddonItemsForGroupRef,
            groupId,
          ),
          from: addonItemsForGroupProvider,
          name: r'addonItemsForGroupProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$addonItemsForGroupHash,
          dependencies: AddonItemsForGroupFamily._dependencies,
          allTransitiveDependencies:
              AddonItemsForGroupFamily._allTransitiveDependencies,
          groupId: groupId,
        );

  AddonItemsForGroupProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.groupId,
  }) : super.internal();

  final String groupId;

  @override
  Override overrideWith(
    FutureOr<List<AddonItemsTableData>> Function(AddonItemsForGroupRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: AddonItemsForGroupProvider._internal(
        (ref) => create(ref as AddonItemsForGroupRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        groupId: groupId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<List<AddonItemsTableData>> createElement() {
    return _AddonItemsForGroupProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is AddonItemsForGroupProvider && other.groupId == groupId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, groupId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin AddonItemsForGroupRef
    on AutoDisposeFutureProviderRef<List<AddonItemsTableData>> {
  /// The parameter `groupId` of this provider.
  String get groupId;
}

class _AddonItemsForGroupProviderElement
    extends AutoDisposeFutureProviderElement<List<AddonItemsTableData>>
    with AddonItemsForGroupRef {
  _AddonItemsForGroupProviderElement(super.provider);

  @override
  String get groupId => (origin as AddonItemsForGroupProvider).groupId;
}

String _$defaultTaxRateHash() => r'a77c9a4a2b8c8824529195cca09873a82fe3f32a';

/// The default tax rate for this branch, or null when none is configured.
///
/// Used during cart construction to pre-fill the tax rate for new sales.
///
/// Copied from [defaultTaxRate].
@ProviderFor(defaultTaxRate)
final defaultTaxRateProvider =
    AutoDisposeFutureProvider<TaxRatesTableData?>.internal(
  defaultTaxRate,
  name: r'defaultTaxRateProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$defaultTaxRateHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef DefaultTaxRateRef = AutoDisposeFutureProviderRef<TaxRatesTableData?>;
String _$activeDealsHash() => r'9ed49f9fcde91f7993e3173865f50495ad1f602b';

/// All currently active deals available for the cashier to apply.
///
/// Copied from [activeDeals].
@ProviderFor(activeDeals)
final activeDealsProvider =
    AutoDisposeFutureProvider<List<DealsTableData>>.internal(
  activeDeals,
  name: r'activeDealsProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$activeDealsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ActiveDealsRef = AutoDisposeFutureProviderRef<List<DealsTableData>>;
String _$activePromotionsHash() => r'36c92046b24d69303e2943ebaeb94e2f34e395da';

/// Active promotions (both automatic and code-triggered).
///
/// Copied from [activePromotions].
@ProviderFor(activePromotions)
final activePromotionsProvider =
    AutoDisposeFutureProvider<List<PromotionsTableData>>.internal(
  activePromotions,
  name: r'activePromotionsProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$activePromotionsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ActivePromotionsRef
    = AutoDisposeFutureProviderRef<List<PromotionsTableData>>;
String _$productStockHash() => r'ef09d24a6e64792163a11c99423b01c85ae0ea3d';

/// Retired product stock map kept for compatibility with older local screens.
/// Active inventory enforcement uses real Variant/VariantBranchStock queries.
///
/// Copied from [productStock].
@ProviderFor(productStock)
final productStockProvider =
    AutoDisposeFutureProvider<Map<String, String>>.internal(
  productStock,
  name: r'productStockProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$productStockHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ProductStockRef = AutoDisposeFutureProviderRef<Map<String, String>>;
String _$posLayoutHash() => r'6d28dcb05319dcd7d5457c760a7074ff140bc4bd';

/// The tenant's Business-Template-driven POS layout (spec Part C / F3/G4) —
/// `'grid_with_variant_picker'` or `'grid_quick_tap'`. Synced from the cloud,
/// cached locally so the POS picks its layout even offline. Defaults to the
/// side-panel layout when unset.
///
/// Copied from [posLayout].
@ProviderFor(posLayout)
final posLayoutProvider = AutoDisposeFutureProvider<String>.internal(
  posLayout,
  name: r'posLayoutProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$posLayoutHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef PosLayoutRef = AutoDisposeFutureProviderRef<String>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
