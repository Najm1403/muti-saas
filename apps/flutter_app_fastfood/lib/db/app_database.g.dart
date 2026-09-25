// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $CategoriesTableTable extends CategoriesTable
    with TableInfo<$CategoriesTableTable, CategoriesTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CategoriesTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _imagePathMeta =
      const VerificationMeta('imagePath');
  @override
  late final GeneratedColumn<String> imagePath = GeneratedColumn<String>(
      'image_path', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _displayOrderMeta =
      const VerificationMeta('displayOrder');
  @override
  late final GeneratedColumn<int> displayOrder = GeneratedColumn<int>(
      'display_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _isActiveMeta =
      const VerificationMeta('isActive');
  @override
  late final GeneratedColumn<bool> isActive = GeneratedColumn<bool>(
      'is_active', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_active" IN (0, 1))'));
  @override
  List<GeneratedColumn> get $columns =>
      [id, name, description, imagePath, displayOrder, isActive];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'categories';
  @override
  VerificationContext validateIntegrity(
      Insertable<CategoriesTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    }
    if (data.containsKey('image_path')) {
      context.handle(_imagePathMeta,
          imagePath.isAcceptableOrUnknown(data['image_path']!, _imagePathMeta));
    }
    if (data.containsKey('display_order')) {
      context.handle(
          _displayOrderMeta,
          displayOrder.isAcceptableOrUnknown(
              data['display_order']!, _displayOrderMeta));
    } else if (isInserting) {
      context.missing(_displayOrderMeta);
    }
    if (data.containsKey('is_active')) {
      context.handle(_isActiveMeta,
          isActive.isAcceptableOrUnknown(data['is_active']!, _isActiveMeta));
    } else if (isInserting) {
      context.missing(_isActiveMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CategoriesTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CategoriesTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description']),
      imagePath: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}image_path']),
      displayOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}display_order'])!,
      isActive: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_active'])!,
    );
  }

  @override
  $CategoriesTableTable createAlias(String alias) {
    return $CategoriesTableTable(attachedDatabase, alias);
  }
}

class CategoriesTableData extends DataClass
    implements Insertable<CategoriesTableData> {
  final String id;
  final String name;
  final String? description;
  final String? imagePath;
  final int displayOrder;
  final bool isActive;
  const CategoriesTableData(
      {required this.id,
      required this.name,
      this.description,
      this.imagePath,
      required this.displayOrder,
      required this.isActive});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    if (!nullToAbsent || imagePath != null) {
      map['image_path'] = Variable<String>(imagePath);
    }
    map['display_order'] = Variable<int>(displayOrder);
    map['is_active'] = Variable<bool>(isActive);
    return map;
  }

  CategoriesTableCompanion toCompanion(bool nullToAbsent) {
    return CategoriesTableCompanion(
      id: Value(id),
      name: Value(name),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      imagePath: imagePath == null && nullToAbsent
          ? const Value.absent()
          : Value(imagePath),
      displayOrder: Value(displayOrder),
      isActive: Value(isActive),
    );
  }

  factory CategoriesTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CategoriesTableData(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      description: serializer.fromJson<String?>(json['description']),
      imagePath: serializer.fromJson<String?>(json['imagePath']),
      displayOrder: serializer.fromJson<int>(json['displayOrder']),
      isActive: serializer.fromJson<bool>(json['isActive']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'description': serializer.toJson<String?>(description),
      'imagePath': serializer.toJson<String?>(imagePath),
      'displayOrder': serializer.toJson<int>(displayOrder),
      'isActive': serializer.toJson<bool>(isActive),
    };
  }

  CategoriesTableData copyWith(
          {String? id,
          String? name,
          Value<String?> description = const Value.absent(),
          Value<String?> imagePath = const Value.absent(),
          int? displayOrder,
          bool? isActive}) =>
      CategoriesTableData(
        id: id ?? this.id,
        name: name ?? this.name,
        description: description.present ? description.value : this.description,
        imagePath: imagePath.present ? imagePath.value : this.imagePath,
        displayOrder: displayOrder ?? this.displayOrder,
        isActive: isActive ?? this.isActive,
      );
  CategoriesTableData copyWithCompanion(CategoriesTableCompanion data) {
    return CategoriesTableData(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      description:
          data.description.present ? data.description.value : this.description,
      imagePath: data.imagePath.present ? data.imagePath.value : this.imagePath,
      displayOrder: data.displayOrder.present
          ? data.displayOrder.value
          : this.displayOrder,
      isActive: data.isActive.present ? data.isActive.value : this.isActive,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CategoriesTableData(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('imagePath: $imagePath, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, name, description, imagePath, displayOrder, isActive);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CategoriesTableData &&
          other.id == this.id &&
          other.name == this.name &&
          other.description == this.description &&
          other.imagePath == this.imagePath &&
          other.displayOrder == this.displayOrder &&
          other.isActive == this.isActive);
}

class CategoriesTableCompanion extends UpdateCompanion<CategoriesTableData> {
  final Value<String> id;
  final Value<String> name;
  final Value<String?> description;
  final Value<String?> imagePath;
  final Value<int> displayOrder;
  final Value<bool> isActive;
  final Value<int> rowid;
  const CategoriesTableCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.description = const Value.absent(),
    this.imagePath = const Value.absent(),
    this.displayOrder = const Value.absent(),
    this.isActive = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CategoriesTableCompanion.insert({
    required String id,
    required String name,
    this.description = const Value.absent(),
    this.imagePath = const Value.absent(),
    required int displayOrder,
    required bool isActive,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        name = Value(name),
        displayOrder = Value(displayOrder),
        isActive = Value(isActive);
  static Insertable<CategoriesTableData> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? description,
    Expression<String>? imagePath,
    Expression<int>? displayOrder,
    Expression<bool>? isActive,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (description != null) 'description': description,
      if (imagePath != null) 'image_path': imagePath,
      if (displayOrder != null) 'display_order': displayOrder,
      if (isActive != null) 'is_active': isActive,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CategoriesTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? name,
      Value<String?>? description,
      Value<String?>? imagePath,
      Value<int>? displayOrder,
      Value<bool>? isActive,
      Value<int>? rowid}) {
    return CategoriesTableCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      imagePath: imagePath ?? this.imagePath,
      displayOrder: displayOrder ?? this.displayOrder,
      isActive: isActive ?? this.isActive,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (imagePath.present) {
      map['image_path'] = Variable<String>(imagePath.value);
    }
    if (displayOrder.present) {
      map['display_order'] = Variable<int>(displayOrder.value);
    }
    if (isActive.present) {
      map['is_active'] = Variable<bool>(isActive.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CategoriesTableCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('imagePath: $imagePath, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ProductsTableTable extends ProductsTable
    with TableInfo<$ProductsTableTable, ProductsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ProductsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _categoryIdMeta =
      const VerificationMeta('categoryId');
  @override
  late final GeneratedColumn<String> categoryId = GeneratedColumn<String>(
      'category_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _productCodeMeta =
      const VerificationMeta('productCode');
  @override
  late final GeneratedColumn<String> productCode = GeneratedColumn<String>(
      'product_code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _basePriceMeta =
      const VerificationMeta('basePrice');
  @override
  late final GeneratedColumn<String> basePrice = GeneratedColumn<String>(
      'base_price', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _imagePathMeta =
      const VerificationMeta('imagePath');
  @override
  late final GeneratedColumn<String> imagePath = GeneratedColumn<String>(
      'image_path', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _displayOrderMeta =
      const VerificationMeta('displayOrder');
  @override
  late final GeneratedColumn<int> displayOrder = GeneratedColumn<int>(
      'display_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _isActiveMeta =
      const VerificationMeta('isActive');
  @override
  late final GeneratedColumn<bool> isActive = GeneratedColumn<bool>(
      'is_active', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_active" IN (0, 1))'));
  static const VerificationMeta _trackInventoryMeta =
      const VerificationMeta('trackInventory');
  @override
  late final GeneratedColumn<bool> trackInventory = GeneratedColumn<bool>(
      'track_inventory', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("track_inventory" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _allowNegativeStockMeta =
      const VerificationMeta('allowNegativeStock');
  @override
  late final GeneratedColumn<bool> allowNegativeStock = GeneratedColumn<bool>(
      'allow_negative_stock', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("allow_negative_stock" IN (0, 1))'),
      defaultValue: const Constant(false));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        categoryId,
        productCode,
        name,
        description,
        basePrice,
        imagePath,
        displayOrder,
        isActive,
        trackInventory,
        allowNegativeStock
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'products';
  @override
  VerificationContext validateIntegrity(Insertable<ProductsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('category_id')) {
      context.handle(
          _categoryIdMeta,
          categoryId.isAcceptableOrUnknown(
              data['category_id']!, _categoryIdMeta));
    } else if (isInserting) {
      context.missing(_categoryIdMeta);
    }
    if (data.containsKey('product_code')) {
      context.handle(
          _productCodeMeta,
          productCode.isAcceptableOrUnknown(
              data['product_code']!, _productCodeMeta));
    } else if (isInserting) {
      context.missing(_productCodeMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    }
    if (data.containsKey('base_price')) {
      context.handle(_basePriceMeta,
          basePrice.isAcceptableOrUnknown(data['base_price']!, _basePriceMeta));
    } else if (isInserting) {
      context.missing(_basePriceMeta);
    }
    if (data.containsKey('image_path')) {
      context.handle(_imagePathMeta,
          imagePath.isAcceptableOrUnknown(data['image_path']!, _imagePathMeta));
    }
    if (data.containsKey('display_order')) {
      context.handle(
          _displayOrderMeta,
          displayOrder.isAcceptableOrUnknown(
              data['display_order']!, _displayOrderMeta));
    } else if (isInserting) {
      context.missing(_displayOrderMeta);
    }
    if (data.containsKey('is_active')) {
      context.handle(_isActiveMeta,
          isActive.isAcceptableOrUnknown(data['is_active']!, _isActiveMeta));
    } else if (isInserting) {
      context.missing(_isActiveMeta);
    }
    if (data.containsKey('track_inventory')) {
      context.handle(
          _trackInventoryMeta,
          trackInventory.isAcceptableOrUnknown(
              data['track_inventory']!, _trackInventoryMeta));
    }
    if (data.containsKey('allow_negative_stock')) {
      context.handle(
          _allowNegativeStockMeta,
          allowNegativeStock.isAcceptableOrUnknown(
              data['allow_negative_stock']!, _allowNegativeStockMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  ProductsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ProductsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      categoryId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}category_id'])!,
      productCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_code'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description']),
      basePrice: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}base_price'])!,
      imagePath: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}image_path']),
      displayOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}display_order'])!,
      isActive: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_active'])!,
      trackInventory: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}track_inventory'])!,
      allowNegativeStock: attachedDatabase.typeMapping.read(
          DriftSqlType.bool, data['${effectivePrefix}allow_negative_stock'])!,
    );
  }

  @override
  $ProductsTableTable createAlias(String alias) {
    return $ProductsTableTable(attachedDatabase, alias);
  }
}

class ProductsTableData extends DataClass
    implements Insertable<ProductsTableData> {
  final String id;
  final String categoryId;
  final String productCode;
  final String name;
  final String? description;

  /// Stored as TEXT to avoid floating-point precision loss.
  final String basePrice;
  final String? imagePath;
  final int displayOrder;
  final bool isActive;

  /// Product-level inventory flags — see LocalProductStockTable for the
  /// actual branch-scoped quantity.
  final bool trackInventory;
  final bool allowNegativeStock;
  const ProductsTableData(
      {required this.id,
      required this.categoryId,
      required this.productCode,
      required this.name,
      this.description,
      required this.basePrice,
      this.imagePath,
      required this.displayOrder,
      required this.isActive,
      required this.trackInventory,
      required this.allowNegativeStock});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['category_id'] = Variable<String>(categoryId);
    map['product_code'] = Variable<String>(productCode);
    map['name'] = Variable<String>(name);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    map['base_price'] = Variable<String>(basePrice);
    if (!nullToAbsent || imagePath != null) {
      map['image_path'] = Variable<String>(imagePath);
    }
    map['display_order'] = Variable<int>(displayOrder);
    map['is_active'] = Variable<bool>(isActive);
    map['track_inventory'] = Variable<bool>(trackInventory);
    map['allow_negative_stock'] = Variable<bool>(allowNegativeStock);
    return map;
  }

  ProductsTableCompanion toCompanion(bool nullToAbsent) {
    return ProductsTableCompanion(
      id: Value(id),
      categoryId: Value(categoryId),
      productCode: Value(productCode),
      name: Value(name),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      basePrice: Value(basePrice),
      imagePath: imagePath == null && nullToAbsent
          ? const Value.absent()
          : Value(imagePath),
      displayOrder: Value(displayOrder),
      isActive: Value(isActive),
      trackInventory: Value(trackInventory),
      allowNegativeStock: Value(allowNegativeStock),
    );
  }

  factory ProductsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ProductsTableData(
      id: serializer.fromJson<String>(json['id']),
      categoryId: serializer.fromJson<String>(json['categoryId']),
      productCode: serializer.fromJson<String>(json['productCode']),
      name: serializer.fromJson<String>(json['name']),
      description: serializer.fromJson<String?>(json['description']),
      basePrice: serializer.fromJson<String>(json['basePrice']),
      imagePath: serializer.fromJson<String?>(json['imagePath']),
      displayOrder: serializer.fromJson<int>(json['displayOrder']),
      isActive: serializer.fromJson<bool>(json['isActive']),
      trackInventory: serializer.fromJson<bool>(json['trackInventory']),
      allowNegativeStock: serializer.fromJson<bool>(json['allowNegativeStock']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'categoryId': serializer.toJson<String>(categoryId),
      'productCode': serializer.toJson<String>(productCode),
      'name': serializer.toJson<String>(name),
      'description': serializer.toJson<String?>(description),
      'basePrice': serializer.toJson<String>(basePrice),
      'imagePath': serializer.toJson<String?>(imagePath),
      'displayOrder': serializer.toJson<int>(displayOrder),
      'isActive': serializer.toJson<bool>(isActive),
      'trackInventory': serializer.toJson<bool>(trackInventory),
      'allowNegativeStock': serializer.toJson<bool>(allowNegativeStock),
    };
  }

  ProductsTableData copyWith(
          {String? id,
          String? categoryId,
          String? productCode,
          String? name,
          Value<String?> description = const Value.absent(),
          String? basePrice,
          Value<String?> imagePath = const Value.absent(),
          int? displayOrder,
          bool? isActive,
          bool? trackInventory,
          bool? allowNegativeStock}) =>
      ProductsTableData(
        id: id ?? this.id,
        categoryId: categoryId ?? this.categoryId,
        productCode: productCode ?? this.productCode,
        name: name ?? this.name,
        description: description.present ? description.value : this.description,
        basePrice: basePrice ?? this.basePrice,
        imagePath: imagePath.present ? imagePath.value : this.imagePath,
        displayOrder: displayOrder ?? this.displayOrder,
        isActive: isActive ?? this.isActive,
        trackInventory: trackInventory ?? this.trackInventory,
        allowNegativeStock: allowNegativeStock ?? this.allowNegativeStock,
      );
  ProductsTableData copyWithCompanion(ProductsTableCompanion data) {
    return ProductsTableData(
      id: data.id.present ? data.id.value : this.id,
      categoryId:
          data.categoryId.present ? data.categoryId.value : this.categoryId,
      productCode:
          data.productCode.present ? data.productCode.value : this.productCode,
      name: data.name.present ? data.name.value : this.name,
      description:
          data.description.present ? data.description.value : this.description,
      basePrice: data.basePrice.present ? data.basePrice.value : this.basePrice,
      imagePath: data.imagePath.present ? data.imagePath.value : this.imagePath,
      displayOrder: data.displayOrder.present
          ? data.displayOrder.value
          : this.displayOrder,
      isActive: data.isActive.present ? data.isActive.value : this.isActive,
      trackInventory: data.trackInventory.present
          ? data.trackInventory.value
          : this.trackInventory,
      allowNegativeStock: data.allowNegativeStock.present
          ? data.allowNegativeStock.value
          : this.allowNegativeStock,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ProductsTableData(')
          ..write('id: $id, ')
          ..write('categoryId: $categoryId, ')
          ..write('productCode: $productCode, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('basePrice: $basePrice, ')
          ..write('imagePath: $imagePath, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive, ')
          ..write('trackInventory: $trackInventory, ')
          ..write('allowNegativeStock: $allowNegativeStock')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      categoryId,
      productCode,
      name,
      description,
      basePrice,
      imagePath,
      displayOrder,
      isActive,
      trackInventory,
      allowNegativeStock);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ProductsTableData &&
          other.id == this.id &&
          other.categoryId == this.categoryId &&
          other.productCode == this.productCode &&
          other.name == this.name &&
          other.description == this.description &&
          other.basePrice == this.basePrice &&
          other.imagePath == this.imagePath &&
          other.displayOrder == this.displayOrder &&
          other.isActive == this.isActive &&
          other.trackInventory == this.trackInventory &&
          other.allowNegativeStock == this.allowNegativeStock);
}

class ProductsTableCompanion extends UpdateCompanion<ProductsTableData> {
  final Value<String> id;
  final Value<String> categoryId;
  final Value<String> productCode;
  final Value<String> name;
  final Value<String?> description;
  final Value<String> basePrice;
  final Value<String?> imagePath;
  final Value<int> displayOrder;
  final Value<bool> isActive;
  final Value<bool> trackInventory;
  final Value<bool> allowNegativeStock;
  final Value<int> rowid;
  const ProductsTableCompanion({
    this.id = const Value.absent(),
    this.categoryId = const Value.absent(),
    this.productCode = const Value.absent(),
    this.name = const Value.absent(),
    this.description = const Value.absent(),
    this.basePrice = const Value.absent(),
    this.imagePath = const Value.absent(),
    this.displayOrder = const Value.absent(),
    this.isActive = const Value.absent(),
    this.trackInventory = const Value.absent(),
    this.allowNegativeStock = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ProductsTableCompanion.insert({
    required String id,
    required String categoryId,
    required String productCode,
    required String name,
    this.description = const Value.absent(),
    required String basePrice,
    this.imagePath = const Value.absent(),
    required int displayOrder,
    required bool isActive,
    this.trackInventory = const Value.absent(),
    this.allowNegativeStock = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        categoryId = Value(categoryId),
        productCode = Value(productCode),
        name = Value(name),
        basePrice = Value(basePrice),
        displayOrder = Value(displayOrder),
        isActive = Value(isActive);
  static Insertable<ProductsTableData> custom({
    Expression<String>? id,
    Expression<String>? categoryId,
    Expression<String>? productCode,
    Expression<String>? name,
    Expression<String>? description,
    Expression<String>? basePrice,
    Expression<String>? imagePath,
    Expression<int>? displayOrder,
    Expression<bool>? isActive,
    Expression<bool>? trackInventory,
    Expression<bool>? allowNegativeStock,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (categoryId != null) 'category_id': categoryId,
      if (productCode != null) 'product_code': productCode,
      if (name != null) 'name': name,
      if (description != null) 'description': description,
      if (basePrice != null) 'base_price': basePrice,
      if (imagePath != null) 'image_path': imagePath,
      if (displayOrder != null) 'display_order': displayOrder,
      if (isActive != null) 'is_active': isActive,
      if (trackInventory != null) 'track_inventory': trackInventory,
      if (allowNegativeStock != null)
        'allow_negative_stock': allowNegativeStock,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ProductsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? categoryId,
      Value<String>? productCode,
      Value<String>? name,
      Value<String?>? description,
      Value<String>? basePrice,
      Value<String?>? imagePath,
      Value<int>? displayOrder,
      Value<bool>? isActive,
      Value<bool>? trackInventory,
      Value<bool>? allowNegativeStock,
      Value<int>? rowid}) {
    return ProductsTableCompanion(
      id: id ?? this.id,
      categoryId: categoryId ?? this.categoryId,
      productCode: productCode ?? this.productCode,
      name: name ?? this.name,
      description: description ?? this.description,
      basePrice: basePrice ?? this.basePrice,
      imagePath: imagePath ?? this.imagePath,
      displayOrder: displayOrder ?? this.displayOrder,
      isActive: isActive ?? this.isActive,
      trackInventory: trackInventory ?? this.trackInventory,
      allowNegativeStock: allowNegativeStock ?? this.allowNegativeStock,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (categoryId.present) {
      map['category_id'] = Variable<String>(categoryId.value);
    }
    if (productCode.present) {
      map['product_code'] = Variable<String>(productCode.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (basePrice.present) {
      map['base_price'] = Variable<String>(basePrice.value);
    }
    if (imagePath.present) {
      map['image_path'] = Variable<String>(imagePath.value);
    }
    if (displayOrder.present) {
      map['display_order'] = Variable<int>(displayOrder.value);
    }
    if (isActive.present) {
      map['is_active'] = Variable<bool>(isActive.value);
    }
    if (trackInventory.present) {
      map['track_inventory'] = Variable<bool>(trackInventory.value);
    }
    if (allowNegativeStock.present) {
      map['allow_negative_stock'] = Variable<bool>(allowNegativeStock.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ProductsTableCompanion(')
          ..write('id: $id, ')
          ..write('categoryId: $categoryId, ')
          ..write('productCode: $productCode, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('basePrice: $basePrice, ')
          ..write('imagePath: $imagePath, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive, ')
          ..write('trackInventory: $trackInventory, ')
          ..write('allowNegativeStock: $allowNegativeStock, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $VariantOptionGroupsTableTable extends VariantOptionGroupsTable
    with
        TableInfo<$VariantOptionGroupsTableTable,
            VariantOptionGroupsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $VariantOptionGroupsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _productIdMeta =
      const VerificationMeta('productId');
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
      'product_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _isRequiredMeta =
      const VerificationMeta('isRequired');
  @override
  late final GeneratedColumn<bool> isRequired = GeneratedColumn<bool>(
      'is_required', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("is_required" IN (0, 1))'));
  static const VerificationMeta _displayOrderMeta =
      const VerificationMeta('displayOrder');
  @override
  late final GeneratedColumn<int> displayOrder = GeneratedColumn<int>(
      'display_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _usageTypeMeta =
      const VerificationMeta('usageType');
  @override
  late final GeneratedColumn<String> usageType = GeneratedColumn<String>(
      'usage_type', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('specification'));
  static const VerificationMeta _allowedOptionIdsMeta =
      const VerificationMeta('allowedOptionIds');
  @override
  late final GeneratedColumn<String> allowedOptionIds = GeneratedColumn<String>(
      'allowed_option_ids', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('[]'));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        productId,
        name,
        isRequired,
        displayOrder,
        usageType,
        allowedOptionIds
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'variant_option_groups';
  @override
  VerificationContext validateIntegrity(
      Insertable<VariantOptionGroupsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('product_id')) {
      context.handle(_productIdMeta,
          productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta));
    } else if (isInserting) {
      context.missing(_productIdMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('is_required')) {
      context.handle(
          _isRequiredMeta,
          isRequired.isAcceptableOrUnknown(
              data['is_required']!, _isRequiredMeta));
    } else if (isInserting) {
      context.missing(_isRequiredMeta);
    }
    if (data.containsKey('display_order')) {
      context.handle(
          _displayOrderMeta,
          displayOrder.isAcceptableOrUnknown(
              data['display_order']!, _displayOrderMeta));
    } else if (isInserting) {
      context.missing(_displayOrderMeta);
    }
    if (data.containsKey('usage_type')) {
      context.handle(_usageTypeMeta,
          usageType.isAcceptableOrUnknown(data['usage_type']!, _usageTypeMeta));
    }
    if (data.containsKey('allowed_option_ids')) {
      context.handle(
          _allowedOptionIdsMeta,
          allowedOptionIds.isAcceptableOrUnknown(
              data['allowed_option_ids']!, _allowedOptionIdsMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  VariantOptionGroupsTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return VariantOptionGroupsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      productId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      isRequired: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_required'])!,
      displayOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}display_order'])!,
      usageType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}usage_type'])!,
      allowedOptionIds: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}allowed_option_ids'])!,
    );
  }

  @override
  $VariantOptionGroupsTableTable createAlias(String alias) {
    return $VariantOptionGroupsTableTable(attachedDatabase, alias);
  }
}

class VariantOptionGroupsTableData extends DataClass
    implements Insertable<VariantOptionGroupsTableData> {
  final String id;
  final String productId;
  final String name;

  /// When true the cashier must pick one option before adding to cart.
  final bool isRequired;
  final int displayOrder;

  /// Laptop Store shareable-inventory model — 'specification' (default,
  /// today's only behavior): options define a combination Variant, unchanged.
  /// 'inventory_component': the POS must offer these options as a dynamic,
  /// independently priced/stocked pick at sale time instead — see
  /// features/pos/widgets/variant_panel.dart's Components section.
  final String usageType;

  /// JSON-encoded list of allowed VariantOption ids for this product's
  /// attachment (spec §22 — compatibility is product-specific). Empty list
  /// (the default) means every option under this group is offered.
  final String allowedOptionIds;
  const VariantOptionGroupsTableData(
      {required this.id,
      required this.productId,
      required this.name,
      required this.isRequired,
      required this.displayOrder,
      required this.usageType,
      required this.allowedOptionIds});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['product_id'] = Variable<String>(productId);
    map['name'] = Variable<String>(name);
    map['is_required'] = Variable<bool>(isRequired);
    map['display_order'] = Variable<int>(displayOrder);
    map['usage_type'] = Variable<String>(usageType);
    map['allowed_option_ids'] = Variable<String>(allowedOptionIds);
    return map;
  }

  VariantOptionGroupsTableCompanion toCompanion(bool nullToAbsent) {
    return VariantOptionGroupsTableCompanion(
      id: Value(id),
      productId: Value(productId),
      name: Value(name),
      isRequired: Value(isRequired),
      displayOrder: Value(displayOrder),
      usageType: Value(usageType),
      allowedOptionIds: Value(allowedOptionIds),
    );
  }

  factory VariantOptionGroupsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return VariantOptionGroupsTableData(
      id: serializer.fromJson<String>(json['id']),
      productId: serializer.fromJson<String>(json['productId']),
      name: serializer.fromJson<String>(json['name']),
      isRequired: serializer.fromJson<bool>(json['isRequired']),
      displayOrder: serializer.fromJson<int>(json['displayOrder']),
      usageType: serializer.fromJson<String>(json['usageType']),
      allowedOptionIds: serializer.fromJson<String>(json['allowedOptionIds']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'productId': serializer.toJson<String>(productId),
      'name': serializer.toJson<String>(name),
      'isRequired': serializer.toJson<bool>(isRequired),
      'displayOrder': serializer.toJson<int>(displayOrder),
      'usageType': serializer.toJson<String>(usageType),
      'allowedOptionIds': serializer.toJson<String>(allowedOptionIds),
    };
  }

  VariantOptionGroupsTableData copyWith(
          {String? id,
          String? productId,
          String? name,
          bool? isRequired,
          int? displayOrder,
          String? usageType,
          String? allowedOptionIds}) =>
      VariantOptionGroupsTableData(
        id: id ?? this.id,
        productId: productId ?? this.productId,
        name: name ?? this.name,
        isRequired: isRequired ?? this.isRequired,
        displayOrder: displayOrder ?? this.displayOrder,
        usageType: usageType ?? this.usageType,
        allowedOptionIds: allowedOptionIds ?? this.allowedOptionIds,
      );
  VariantOptionGroupsTableData copyWithCompanion(
      VariantOptionGroupsTableCompanion data) {
    return VariantOptionGroupsTableData(
      id: data.id.present ? data.id.value : this.id,
      productId: data.productId.present ? data.productId.value : this.productId,
      name: data.name.present ? data.name.value : this.name,
      isRequired:
          data.isRequired.present ? data.isRequired.value : this.isRequired,
      displayOrder: data.displayOrder.present
          ? data.displayOrder.value
          : this.displayOrder,
      usageType: data.usageType.present ? data.usageType.value : this.usageType,
      allowedOptionIds: data.allowedOptionIds.present
          ? data.allowedOptionIds.value
          : this.allowedOptionIds,
    );
  }

  @override
  String toString() {
    return (StringBuffer('VariantOptionGroupsTableData(')
          ..write('id: $id, ')
          ..write('productId: $productId, ')
          ..write('name: $name, ')
          ..write('isRequired: $isRequired, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('usageType: $usageType, ')
          ..write('allowedOptionIds: $allowedOptionIds')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, productId, name, isRequired, displayOrder,
      usageType, allowedOptionIds);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is VariantOptionGroupsTableData &&
          other.id == this.id &&
          other.productId == this.productId &&
          other.name == this.name &&
          other.isRequired == this.isRequired &&
          other.displayOrder == this.displayOrder &&
          other.usageType == this.usageType &&
          other.allowedOptionIds == this.allowedOptionIds);
}

class VariantOptionGroupsTableCompanion
    extends UpdateCompanion<VariantOptionGroupsTableData> {
  final Value<String> id;
  final Value<String> productId;
  final Value<String> name;
  final Value<bool> isRequired;
  final Value<int> displayOrder;
  final Value<String> usageType;
  final Value<String> allowedOptionIds;
  final Value<int> rowid;
  const VariantOptionGroupsTableCompanion({
    this.id = const Value.absent(),
    this.productId = const Value.absent(),
    this.name = const Value.absent(),
    this.isRequired = const Value.absent(),
    this.displayOrder = const Value.absent(),
    this.usageType = const Value.absent(),
    this.allowedOptionIds = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  VariantOptionGroupsTableCompanion.insert({
    required String id,
    required String productId,
    required String name,
    required bool isRequired,
    required int displayOrder,
    this.usageType = const Value.absent(),
    this.allowedOptionIds = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        productId = Value(productId),
        name = Value(name),
        isRequired = Value(isRequired),
        displayOrder = Value(displayOrder);
  static Insertable<VariantOptionGroupsTableData> custom({
    Expression<String>? id,
    Expression<String>? productId,
    Expression<String>? name,
    Expression<bool>? isRequired,
    Expression<int>? displayOrder,
    Expression<String>? usageType,
    Expression<String>? allowedOptionIds,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (productId != null) 'product_id': productId,
      if (name != null) 'name': name,
      if (isRequired != null) 'is_required': isRequired,
      if (displayOrder != null) 'display_order': displayOrder,
      if (usageType != null) 'usage_type': usageType,
      if (allowedOptionIds != null) 'allowed_option_ids': allowedOptionIds,
      if (rowid != null) 'rowid': rowid,
    });
  }

  VariantOptionGroupsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? productId,
      Value<String>? name,
      Value<bool>? isRequired,
      Value<int>? displayOrder,
      Value<String>? usageType,
      Value<String>? allowedOptionIds,
      Value<int>? rowid}) {
    return VariantOptionGroupsTableCompanion(
      id: id ?? this.id,
      productId: productId ?? this.productId,
      name: name ?? this.name,
      isRequired: isRequired ?? this.isRequired,
      displayOrder: displayOrder ?? this.displayOrder,
      usageType: usageType ?? this.usageType,
      allowedOptionIds: allowedOptionIds ?? this.allowedOptionIds,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (isRequired.present) {
      map['is_required'] = Variable<bool>(isRequired.value);
    }
    if (displayOrder.present) {
      map['display_order'] = Variable<int>(displayOrder.value);
    }
    if (usageType.present) {
      map['usage_type'] = Variable<String>(usageType.value);
    }
    if (allowedOptionIds.present) {
      map['allowed_option_ids'] = Variable<String>(allowedOptionIds.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('VariantOptionGroupsTableCompanion(')
          ..write('id: $id, ')
          ..write('productId: $productId, ')
          ..write('name: $name, ')
          ..write('isRequired: $isRequired, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('usageType: $usageType, ')
          ..write('allowedOptionIds: $allowedOptionIds, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $VariantOptionsTableTable extends VariantOptionsTable
    with TableInfo<$VariantOptionsTableTable, VariantOptionsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $VariantOptionsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _optionGroupIdMeta =
      const VerificationMeta('optionGroupId');
  @override
  late final GeneratedColumn<String> optionGroupId = GeneratedColumn<String>(
      'option_group_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _displayOrderMeta =
      const VerificationMeta('displayOrder');
  @override
  late final GeneratedColumn<int> displayOrder = GeneratedColumn<int>(
      'display_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _isActiveMeta =
      const VerificationMeta('isActive');
  @override
  late final GeneratedColumn<bool> isActive = GeneratedColumn<bool>(
      'is_active', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_active" IN (0, 1))'));
  static const VerificationMeta _componentVariantIdMeta =
      const VerificationMeta('componentVariantId');
  @override
  late final GeneratedColumn<String> componentVariantId =
      GeneratedColumn<String>('component_variant_id', aliasedName, true,
          type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [id, optionGroupId, name, displayOrder, isActive, componentVariantId];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'variant_options';
  @override
  VerificationContext validateIntegrity(
      Insertable<VariantOptionsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('option_group_id')) {
      context.handle(
          _optionGroupIdMeta,
          optionGroupId.isAcceptableOrUnknown(
              data['option_group_id']!, _optionGroupIdMeta));
    } else if (isInserting) {
      context.missing(_optionGroupIdMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('display_order')) {
      context.handle(
          _displayOrderMeta,
          displayOrder.isAcceptableOrUnknown(
              data['display_order']!, _displayOrderMeta));
    } else if (isInserting) {
      context.missing(_displayOrderMeta);
    }
    if (data.containsKey('is_active')) {
      context.handle(_isActiveMeta,
          isActive.isAcceptableOrUnknown(data['is_active']!, _isActiveMeta));
    } else if (isInserting) {
      context.missing(_isActiveMeta);
    }
    if (data.containsKey('component_variant_id')) {
      context.handle(
          _componentVariantIdMeta,
          componentVariantId.isAcceptableOrUnknown(
              data['component_variant_id']!, _componentVariantIdMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  VariantOptionsTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return VariantOptionsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      optionGroupId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}option_group_id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      displayOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}display_order'])!,
      isActive: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_active'])!,
      componentVariantId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}component_variant_id']),
    );
  }

  @override
  $VariantOptionsTableTable createAlias(String alias) {
    return $VariantOptionsTableTable(attachedDatabase, alias);
  }
}

class VariantOptionsTableData extends DataClass
    implements Insertable<VariantOptionsTableData> {
  final String id;
  final String optionGroupId;
  final String name;
  final int displayOrder;
  final bool isActive;

  /// Laptop Store shareable-inventory model — set only when this option is
  /// tracked as a shared inventory component. Resolves this option's own
  /// price/stock via [VariantsTable] (the component's own real Variant) —
  /// no separate data source needed.
  final String? componentVariantId;
  const VariantOptionsTableData(
      {required this.id,
      required this.optionGroupId,
      required this.name,
      required this.displayOrder,
      required this.isActive,
      this.componentVariantId});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['option_group_id'] = Variable<String>(optionGroupId);
    map['name'] = Variable<String>(name);
    map['display_order'] = Variable<int>(displayOrder);
    map['is_active'] = Variable<bool>(isActive);
    if (!nullToAbsent || componentVariantId != null) {
      map['component_variant_id'] = Variable<String>(componentVariantId);
    }
    return map;
  }

  VariantOptionsTableCompanion toCompanion(bool nullToAbsent) {
    return VariantOptionsTableCompanion(
      id: Value(id),
      optionGroupId: Value(optionGroupId),
      name: Value(name),
      displayOrder: Value(displayOrder),
      isActive: Value(isActive),
      componentVariantId: componentVariantId == null && nullToAbsent
          ? const Value.absent()
          : Value(componentVariantId),
    );
  }

  factory VariantOptionsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return VariantOptionsTableData(
      id: serializer.fromJson<String>(json['id']),
      optionGroupId: serializer.fromJson<String>(json['optionGroupId']),
      name: serializer.fromJson<String>(json['name']),
      displayOrder: serializer.fromJson<int>(json['displayOrder']),
      isActive: serializer.fromJson<bool>(json['isActive']),
      componentVariantId:
          serializer.fromJson<String?>(json['componentVariantId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'optionGroupId': serializer.toJson<String>(optionGroupId),
      'name': serializer.toJson<String>(name),
      'displayOrder': serializer.toJson<int>(displayOrder),
      'isActive': serializer.toJson<bool>(isActive),
      'componentVariantId': serializer.toJson<String?>(componentVariantId),
    };
  }

  VariantOptionsTableData copyWith(
          {String? id,
          String? optionGroupId,
          String? name,
          int? displayOrder,
          bool? isActive,
          Value<String?> componentVariantId = const Value.absent()}) =>
      VariantOptionsTableData(
        id: id ?? this.id,
        optionGroupId: optionGroupId ?? this.optionGroupId,
        name: name ?? this.name,
        displayOrder: displayOrder ?? this.displayOrder,
        isActive: isActive ?? this.isActive,
        componentVariantId: componentVariantId.present
            ? componentVariantId.value
            : this.componentVariantId,
      );
  VariantOptionsTableData copyWithCompanion(VariantOptionsTableCompanion data) {
    return VariantOptionsTableData(
      id: data.id.present ? data.id.value : this.id,
      optionGroupId: data.optionGroupId.present
          ? data.optionGroupId.value
          : this.optionGroupId,
      name: data.name.present ? data.name.value : this.name,
      displayOrder: data.displayOrder.present
          ? data.displayOrder.value
          : this.displayOrder,
      isActive: data.isActive.present ? data.isActive.value : this.isActive,
      componentVariantId: data.componentVariantId.present
          ? data.componentVariantId.value
          : this.componentVariantId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('VariantOptionsTableData(')
          ..write('id: $id, ')
          ..write('optionGroupId: $optionGroupId, ')
          ..write('name: $name, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive, ')
          ..write('componentVariantId: $componentVariantId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, optionGroupId, name, displayOrder, isActive, componentVariantId);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is VariantOptionsTableData &&
          other.id == this.id &&
          other.optionGroupId == this.optionGroupId &&
          other.name == this.name &&
          other.displayOrder == this.displayOrder &&
          other.isActive == this.isActive &&
          other.componentVariantId == this.componentVariantId);
}

class VariantOptionsTableCompanion
    extends UpdateCompanion<VariantOptionsTableData> {
  final Value<String> id;
  final Value<String> optionGroupId;
  final Value<String> name;
  final Value<int> displayOrder;
  final Value<bool> isActive;
  final Value<String?> componentVariantId;
  final Value<int> rowid;
  const VariantOptionsTableCompanion({
    this.id = const Value.absent(),
    this.optionGroupId = const Value.absent(),
    this.name = const Value.absent(),
    this.displayOrder = const Value.absent(),
    this.isActive = const Value.absent(),
    this.componentVariantId = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  VariantOptionsTableCompanion.insert({
    required String id,
    required String optionGroupId,
    required String name,
    required int displayOrder,
    required bool isActive,
    this.componentVariantId = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        optionGroupId = Value(optionGroupId),
        name = Value(name),
        displayOrder = Value(displayOrder),
        isActive = Value(isActive);
  static Insertable<VariantOptionsTableData> custom({
    Expression<String>? id,
    Expression<String>? optionGroupId,
    Expression<String>? name,
    Expression<int>? displayOrder,
    Expression<bool>? isActive,
    Expression<String>? componentVariantId,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (optionGroupId != null) 'option_group_id': optionGroupId,
      if (name != null) 'name': name,
      if (displayOrder != null) 'display_order': displayOrder,
      if (isActive != null) 'is_active': isActive,
      if (componentVariantId != null)
        'component_variant_id': componentVariantId,
      if (rowid != null) 'rowid': rowid,
    });
  }

  VariantOptionsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? optionGroupId,
      Value<String>? name,
      Value<int>? displayOrder,
      Value<bool>? isActive,
      Value<String?>? componentVariantId,
      Value<int>? rowid}) {
    return VariantOptionsTableCompanion(
      id: id ?? this.id,
      optionGroupId: optionGroupId ?? this.optionGroupId,
      name: name ?? this.name,
      displayOrder: displayOrder ?? this.displayOrder,
      isActive: isActive ?? this.isActive,
      componentVariantId: componentVariantId ?? this.componentVariantId,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (optionGroupId.present) {
      map['option_group_id'] = Variable<String>(optionGroupId.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (displayOrder.present) {
      map['display_order'] = Variable<int>(displayOrder.value);
    }
    if (isActive.present) {
      map['is_active'] = Variable<bool>(isActive.value);
    }
    if (componentVariantId.present) {
      map['component_variant_id'] = Variable<String>(componentVariantId.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('VariantOptionsTableCompanion(')
          ..write('id: $id, ')
          ..write('optionGroupId: $optionGroupId, ')
          ..write('name: $name, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive, ')
          ..write('componentVariantId: $componentVariantId, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $VariantsTableTable extends VariantsTable
    with TableInfo<$VariantsTableTable, VariantsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $VariantsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _productIdMeta =
      const VerificationMeta('productId');
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
      'product_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _optionValueIdsMeta =
      const VerificationMeta('optionValueIds');
  @override
  late final GeneratedColumn<String> optionValueIds = GeneratedColumn<String>(
      'option_value_ids', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _salePriceMeta =
      const VerificationMeta('salePrice');
  @override
  late final GeneratedColumn<String> salePrice = GeneratedColumn<String>(
      'sale_price', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _costPriceMeta =
      const VerificationMeta('costPrice');
  @override
  late final GeneratedColumn<String> costPrice = GeneratedColumn<String>(
      'cost_price', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _comparePriceMeta =
      const VerificationMeta('comparePrice');
  @override
  late final GeneratedColumn<String> comparePrice = GeneratedColumn<String>(
      'compare_price', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _tracksInventoryMeta =
      const VerificationMeta('tracksInventory');
  @override
  late final GeneratedColumn<bool> tracksInventory = GeneratedColumn<bool>(
      'tracks_inventory', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("tracks_inventory" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _isDefaultMeta =
      const VerificationMeta('isDefault');
  @override
  late final GeneratedColumn<bool> isDefault = GeneratedColumn<bool>(
      'is_default', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_default" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _sellableMeta =
      const VerificationMeta('sellable');
  @override
  late final GeneratedColumn<bool> sellable = GeneratedColumn<bool>(
      'sellable', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("sellable" IN (0, 1))'),
      defaultValue: const Constant(true));
  static const VerificationMeta _sellableReasonMeta =
      const VerificationMeta('sellableReason');
  @override
  late final GeneratedColumn<String> sellableReason = GeneratedColumn<String>(
      'sellable_reason', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _allowInventoryTrackingMeta =
      const VerificationMeta('allowInventoryTracking');
  @override
  late final GeneratedColumn<bool> allowInventoryTracking =
      GeneratedColumn<bool>('allow_inventory_tracking', aliasedName, false,
          type: DriftSqlType.bool,
          requiredDuringInsert: false,
          defaultConstraints: GeneratedColumn.constraintIsAlways(
              'CHECK ("allow_inventory_tracking" IN (0, 1))'),
          defaultValue: const Constant(false));
  static const VerificationMeta _productNameMeta =
      const VerificationMeta('productName');
  @override
  late final GeneratedColumn<String> productName = GeneratedColumn<String>(
      'product_name', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _variantNameMeta =
      const VerificationMeta('variantName');
  @override
  late final GeneratedColumn<String> variantName = GeneratedColumn<String>(
      'variant_name', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        productId,
        optionValueIds,
        salePrice,
        costPrice,
        comparePrice,
        tracksInventory,
        isDefault,
        sellable,
        sellableReason,
        allowInventoryTracking,
        productName,
        variantName
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'variants';
  @override
  VerificationContext validateIntegrity(Insertable<VariantsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('product_id')) {
      context.handle(_productIdMeta,
          productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta));
    } else if (isInserting) {
      context.missing(_productIdMeta);
    }
    if (data.containsKey('option_value_ids')) {
      context.handle(
          _optionValueIdsMeta,
          optionValueIds.isAcceptableOrUnknown(
              data['option_value_ids']!, _optionValueIdsMeta));
    } else if (isInserting) {
      context.missing(_optionValueIdsMeta);
    }
    if (data.containsKey('sale_price')) {
      context.handle(_salePriceMeta,
          salePrice.isAcceptableOrUnknown(data['sale_price']!, _salePriceMeta));
    } else if (isInserting) {
      context.missing(_salePriceMeta);
    }
    if (data.containsKey('cost_price')) {
      context.handle(_costPriceMeta,
          costPrice.isAcceptableOrUnknown(data['cost_price']!, _costPriceMeta));
    }
    if (data.containsKey('compare_price')) {
      context.handle(
          _comparePriceMeta,
          comparePrice.isAcceptableOrUnknown(
              data['compare_price']!, _comparePriceMeta));
    }
    if (data.containsKey('tracks_inventory')) {
      context.handle(
          _tracksInventoryMeta,
          tracksInventory.isAcceptableOrUnknown(
              data['tracks_inventory']!, _tracksInventoryMeta));
    }
    if (data.containsKey('is_default')) {
      context.handle(_isDefaultMeta,
          isDefault.isAcceptableOrUnknown(data['is_default']!, _isDefaultMeta));
    }
    if (data.containsKey('sellable')) {
      context.handle(_sellableMeta,
          sellable.isAcceptableOrUnknown(data['sellable']!, _sellableMeta));
    }
    if (data.containsKey('sellable_reason')) {
      context.handle(
          _sellableReasonMeta,
          sellableReason.isAcceptableOrUnknown(
              data['sellable_reason']!, _sellableReasonMeta));
    }
    if (data.containsKey('allow_inventory_tracking')) {
      context.handle(
          _allowInventoryTrackingMeta,
          allowInventoryTracking.isAcceptableOrUnknown(
              data['allow_inventory_tracking']!, _allowInventoryTrackingMeta));
    }
    if (data.containsKey('product_name')) {
      context.handle(
          _productNameMeta,
          productName.isAcceptableOrUnknown(
              data['product_name']!, _productNameMeta));
    }
    if (data.containsKey('variant_name')) {
      context.handle(
          _variantNameMeta,
          variantName.isAcceptableOrUnknown(
              data['variant_name']!, _variantNameMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  VariantsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return VariantsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      productId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_id'])!,
      optionValueIds: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}option_value_ids'])!,
      salePrice: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sale_price'])!,
      costPrice: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}cost_price']),
      comparePrice: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}compare_price']),
      tracksInventory: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}tracks_inventory'])!,
      isDefault: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_default'])!,
      sellable: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}sellable'])!,
      sellableReason: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sellable_reason']),
      allowInventoryTracking: attachedDatabase.typeMapping.read(
          DriftSqlType.bool,
          data['${effectivePrefix}allow_inventory_tracking'])!,
      productName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_name']),
      variantName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}variant_name']),
    );
  }

  @override
  $VariantsTableTable createAlias(String alias) {
    return $VariantsTableTable(attachedDatabase, alias);
  }
}

class VariantsTableData extends DataClass
    implements Insertable<VariantsTableData> {
  final String id;
  final String productId;

  /// JSON-encoded list of VariantOption ids composing this SKU.
  final String optionValueIds;
  final String salePrice;
  final String? costPrice;
  final String? comparePrice;
  final bool tracksInventory;
  final bool isDefault;

  /// Server-computed sellability (e.g. false when required groups can't be
  /// satisfied). The POS must never synthesize a variant client-side — only
  /// ever match against rows synced here.
  final bool sellable;

  /// Human-readable reason when [sellable] is false (e.g. "missing a
  /// selection for a required Variant Option Group"), so the cashier sees
  /// the real cause instead of a generic message. Null when sellable.
  final String? sellableReason;

  /// Product-level master inventory switch, denormalized here for convenience
  /// so stock checks don't need a join back to [ProductsTable].
  final bool allowInventoryTracking;
  final String? productName;
  final String? variantName;
  const VariantsTableData(
      {required this.id,
      required this.productId,
      required this.optionValueIds,
      required this.salePrice,
      this.costPrice,
      this.comparePrice,
      required this.tracksInventory,
      required this.isDefault,
      required this.sellable,
      this.sellableReason,
      required this.allowInventoryTracking,
      this.productName,
      this.variantName});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['product_id'] = Variable<String>(productId);
    map['option_value_ids'] = Variable<String>(optionValueIds);
    map['sale_price'] = Variable<String>(salePrice);
    if (!nullToAbsent || costPrice != null) {
      map['cost_price'] = Variable<String>(costPrice);
    }
    if (!nullToAbsent || comparePrice != null) {
      map['compare_price'] = Variable<String>(comparePrice);
    }
    map['tracks_inventory'] = Variable<bool>(tracksInventory);
    map['is_default'] = Variable<bool>(isDefault);
    map['sellable'] = Variable<bool>(sellable);
    if (!nullToAbsent || sellableReason != null) {
      map['sellable_reason'] = Variable<String>(sellableReason);
    }
    map['allow_inventory_tracking'] = Variable<bool>(allowInventoryTracking);
    if (!nullToAbsent || productName != null) {
      map['product_name'] = Variable<String>(productName);
    }
    if (!nullToAbsent || variantName != null) {
      map['variant_name'] = Variable<String>(variantName);
    }
    return map;
  }

  VariantsTableCompanion toCompanion(bool nullToAbsent) {
    return VariantsTableCompanion(
      id: Value(id),
      productId: Value(productId),
      optionValueIds: Value(optionValueIds),
      salePrice: Value(salePrice),
      costPrice: costPrice == null && nullToAbsent
          ? const Value.absent()
          : Value(costPrice),
      comparePrice: comparePrice == null && nullToAbsent
          ? const Value.absent()
          : Value(comparePrice),
      tracksInventory: Value(tracksInventory),
      isDefault: Value(isDefault),
      sellable: Value(sellable),
      sellableReason: sellableReason == null && nullToAbsent
          ? const Value.absent()
          : Value(sellableReason),
      allowInventoryTracking: Value(allowInventoryTracking),
      productName: productName == null && nullToAbsent
          ? const Value.absent()
          : Value(productName),
      variantName: variantName == null && nullToAbsent
          ? const Value.absent()
          : Value(variantName),
    );
  }

  factory VariantsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return VariantsTableData(
      id: serializer.fromJson<String>(json['id']),
      productId: serializer.fromJson<String>(json['productId']),
      optionValueIds: serializer.fromJson<String>(json['optionValueIds']),
      salePrice: serializer.fromJson<String>(json['salePrice']),
      costPrice: serializer.fromJson<String?>(json['costPrice']),
      comparePrice: serializer.fromJson<String?>(json['comparePrice']),
      tracksInventory: serializer.fromJson<bool>(json['tracksInventory']),
      isDefault: serializer.fromJson<bool>(json['isDefault']),
      sellable: serializer.fromJson<bool>(json['sellable']),
      sellableReason: serializer.fromJson<String?>(json['sellableReason']),
      allowInventoryTracking:
          serializer.fromJson<bool>(json['allowInventoryTracking']),
      productName: serializer.fromJson<String?>(json['productName']),
      variantName: serializer.fromJson<String?>(json['variantName']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'productId': serializer.toJson<String>(productId),
      'optionValueIds': serializer.toJson<String>(optionValueIds),
      'salePrice': serializer.toJson<String>(salePrice),
      'costPrice': serializer.toJson<String?>(costPrice),
      'comparePrice': serializer.toJson<String?>(comparePrice),
      'tracksInventory': serializer.toJson<bool>(tracksInventory),
      'isDefault': serializer.toJson<bool>(isDefault),
      'sellable': serializer.toJson<bool>(sellable),
      'sellableReason': serializer.toJson<String?>(sellableReason),
      'allowInventoryTracking': serializer.toJson<bool>(allowInventoryTracking),
      'productName': serializer.toJson<String?>(productName),
      'variantName': serializer.toJson<String?>(variantName),
    };
  }

  VariantsTableData copyWith(
          {String? id,
          String? productId,
          String? optionValueIds,
          String? salePrice,
          Value<String?> costPrice = const Value.absent(),
          Value<String?> comparePrice = const Value.absent(),
          bool? tracksInventory,
          bool? isDefault,
          bool? sellable,
          Value<String?> sellableReason = const Value.absent(),
          bool? allowInventoryTracking,
          Value<String?> productName = const Value.absent(),
          Value<String?> variantName = const Value.absent()}) =>
      VariantsTableData(
        id: id ?? this.id,
        productId: productId ?? this.productId,
        optionValueIds: optionValueIds ?? this.optionValueIds,
        salePrice: salePrice ?? this.salePrice,
        costPrice: costPrice.present ? costPrice.value : this.costPrice,
        comparePrice:
            comparePrice.present ? comparePrice.value : this.comparePrice,
        tracksInventory: tracksInventory ?? this.tracksInventory,
        isDefault: isDefault ?? this.isDefault,
        sellable: sellable ?? this.sellable,
        sellableReason:
            sellableReason.present ? sellableReason.value : this.sellableReason,
        allowInventoryTracking:
            allowInventoryTracking ?? this.allowInventoryTracking,
        productName: productName.present ? productName.value : this.productName,
        variantName: variantName.present ? variantName.value : this.variantName,
      );
  VariantsTableData copyWithCompanion(VariantsTableCompanion data) {
    return VariantsTableData(
      id: data.id.present ? data.id.value : this.id,
      productId: data.productId.present ? data.productId.value : this.productId,
      optionValueIds: data.optionValueIds.present
          ? data.optionValueIds.value
          : this.optionValueIds,
      salePrice: data.salePrice.present ? data.salePrice.value : this.salePrice,
      costPrice: data.costPrice.present ? data.costPrice.value : this.costPrice,
      comparePrice: data.comparePrice.present
          ? data.comparePrice.value
          : this.comparePrice,
      tracksInventory: data.tracksInventory.present
          ? data.tracksInventory.value
          : this.tracksInventory,
      isDefault: data.isDefault.present ? data.isDefault.value : this.isDefault,
      sellable: data.sellable.present ? data.sellable.value : this.sellable,
      sellableReason: data.sellableReason.present
          ? data.sellableReason.value
          : this.sellableReason,
      allowInventoryTracking: data.allowInventoryTracking.present
          ? data.allowInventoryTracking.value
          : this.allowInventoryTracking,
      productName:
          data.productName.present ? data.productName.value : this.productName,
      variantName:
          data.variantName.present ? data.variantName.value : this.variantName,
    );
  }

  @override
  String toString() {
    return (StringBuffer('VariantsTableData(')
          ..write('id: $id, ')
          ..write('productId: $productId, ')
          ..write('optionValueIds: $optionValueIds, ')
          ..write('salePrice: $salePrice, ')
          ..write('costPrice: $costPrice, ')
          ..write('comparePrice: $comparePrice, ')
          ..write('tracksInventory: $tracksInventory, ')
          ..write('isDefault: $isDefault, ')
          ..write('sellable: $sellable, ')
          ..write('sellableReason: $sellableReason, ')
          ..write('allowInventoryTracking: $allowInventoryTracking, ')
          ..write('productName: $productName, ')
          ..write('variantName: $variantName')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      productId,
      optionValueIds,
      salePrice,
      costPrice,
      comparePrice,
      tracksInventory,
      isDefault,
      sellable,
      sellableReason,
      allowInventoryTracking,
      productName,
      variantName);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is VariantsTableData &&
          other.id == this.id &&
          other.productId == this.productId &&
          other.optionValueIds == this.optionValueIds &&
          other.salePrice == this.salePrice &&
          other.costPrice == this.costPrice &&
          other.comparePrice == this.comparePrice &&
          other.tracksInventory == this.tracksInventory &&
          other.isDefault == this.isDefault &&
          other.sellable == this.sellable &&
          other.sellableReason == this.sellableReason &&
          other.allowInventoryTracking == this.allowInventoryTracking &&
          other.productName == this.productName &&
          other.variantName == this.variantName);
}

class VariantsTableCompanion extends UpdateCompanion<VariantsTableData> {
  final Value<String> id;
  final Value<String> productId;
  final Value<String> optionValueIds;
  final Value<String> salePrice;
  final Value<String?> costPrice;
  final Value<String?> comparePrice;
  final Value<bool> tracksInventory;
  final Value<bool> isDefault;
  final Value<bool> sellable;
  final Value<String?> sellableReason;
  final Value<bool> allowInventoryTracking;
  final Value<String?> productName;
  final Value<String?> variantName;
  final Value<int> rowid;
  const VariantsTableCompanion({
    this.id = const Value.absent(),
    this.productId = const Value.absent(),
    this.optionValueIds = const Value.absent(),
    this.salePrice = const Value.absent(),
    this.costPrice = const Value.absent(),
    this.comparePrice = const Value.absent(),
    this.tracksInventory = const Value.absent(),
    this.isDefault = const Value.absent(),
    this.sellable = const Value.absent(),
    this.sellableReason = const Value.absent(),
    this.allowInventoryTracking = const Value.absent(),
    this.productName = const Value.absent(),
    this.variantName = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  VariantsTableCompanion.insert({
    required String id,
    required String productId,
    required String optionValueIds,
    required String salePrice,
    this.costPrice = const Value.absent(),
    this.comparePrice = const Value.absent(),
    this.tracksInventory = const Value.absent(),
    this.isDefault = const Value.absent(),
    this.sellable = const Value.absent(),
    this.sellableReason = const Value.absent(),
    this.allowInventoryTracking = const Value.absent(),
    this.productName = const Value.absent(),
    this.variantName = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        productId = Value(productId),
        optionValueIds = Value(optionValueIds),
        salePrice = Value(salePrice);
  static Insertable<VariantsTableData> custom({
    Expression<String>? id,
    Expression<String>? productId,
    Expression<String>? optionValueIds,
    Expression<String>? salePrice,
    Expression<String>? costPrice,
    Expression<String>? comparePrice,
    Expression<bool>? tracksInventory,
    Expression<bool>? isDefault,
    Expression<bool>? sellable,
    Expression<String>? sellableReason,
    Expression<bool>? allowInventoryTracking,
    Expression<String>? productName,
    Expression<String>? variantName,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (productId != null) 'product_id': productId,
      if (optionValueIds != null) 'option_value_ids': optionValueIds,
      if (salePrice != null) 'sale_price': salePrice,
      if (costPrice != null) 'cost_price': costPrice,
      if (comparePrice != null) 'compare_price': comparePrice,
      if (tracksInventory != null) 'tracks_inventory': tracksInventory,
      if (isDefault != null) 'is_default': isDefault,
      if (sellable != null) 'sellable': sellable,
      if (sellableReason != null) 'sellable_reason': sellableReason,
      if (allowInventoryTracking != null)
        'allow_inventory_tracking': allowInventoryTracking,
      if (productName != null) 'product_name': productName,
      if (variantName != null) 'variant_name': variantName,
      if (rowid != null) 'rowid': rowid,
    });
  }

  VariantsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? productId,
      Value<String>? optionValueIds,
      Value<String>? salePrice,
      Value<String?>? costPrice,
      Value<String?>? comparePrice,
      Value<bool>? tracksInventory,
      Value<bool>? isDefault,
      Value<bool>? sellable,
      Value<String?>? sellableReason,
      Value<bool>? allowInventoryTracking,
      Value<String?>? productName,
      Value<String?>? variantName,
      Value<int>? rowid}) {
    return VariantsTableCompanion(
      id: id ?? this.id,
      productId: productId ?? this.productId,
      optionValueIds: optionValueIds ?? this.optionValueIds,
      salePrice: salePrice ?? this.salePrice,
      costPrice: costPrice ?? this.costPrice,
      comparePrice: comparePrice ?? this.comparePrice,
      tracksInventory: tracksInventory ?? this.tracksInventory,
      isDefault: isDefault ?? this.isDefault,
      sellable: sellable ?? this.sellable,
      sellableReason: sellableReason ?? this.sellableReason,
      allowInventoryTracking:
          allowInventoryTracking ?? this.allowInventoryTracking,
      productName: productName ?? this.productName,
      variantName: variantName ?? this.variantName,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (optionValueIds.present) {
      map['option_value_ids'] = Variable<String>(optionValueIds.value);
    }
    if (salePrice.present) {
      map['sale_price'] = Variable<String>(salePrice.value);
    }
    if (costPrice.present) {
      map['cost_price'] = Variable<String>(costPrice.value);
    }
    if (comparePrice.present) {
      map['compare_price'] = Variable<String>(comparePrice.value);
    }
    if (tracksInventory.present) {
      map['tracks_inventory'] = Variable<bool>(tracksInventory.value);
    }
    if (isDefault.present) {
      map['is_default'] = Variable<bool>(isDefault.value);
    }
    if (sellable.present) {
      map['sellable'] = Variable<bool>(sellable.value);
    }
    if (sellableReason.present) {
      map['sellable_reason'] = Variable<String>(sellableReason.value);
    }
    if (allowInventoryTracking.present) {
      map['allow_inventory_tracking'] =
          Variable<bool>(allowInventoryTracking.value);
    }
    if (productName.present) {
      map['product_name'] = Variable<String>(productName.value);
    }
    if (variantName.present) {
      map['variant_name'] = Variable<String>(variantName.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('VariantsTableCompanion(')
          ..write('id: $id, ')
          ..write('productId: $productId, ')
          ..write('optionValueIds: $optionValueIds, ')
          ..write('salePrice: $salePrice, ')
          ..write('costPrice: $costPrice, ')
          ..write('comparePrice: $comparePrice, ')
          ..write('tracksInventory: $tracksInventory, ')
          ..write('isDefault: $isDefault, ')
          ..write('sellable: $sellable, ')
          ..write('sellableReason: $sellableReason, ')
          ..write('allowInventoryTracking: $allowInventoryTracking, ')
          ..write('productName: $productName, ')
          ..write('variantName: $variantName, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $VariantBranchStockTableTable extends VariantBranchStockTable
    with TableInfo<$VariantBranchStockTableTable, VariantBranchStockTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $VariantBranchStockTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _variantIdMeta =
      const VerificationMeta('variantId');
  @override
  late final GeneratedColumn<String> variantId = GeneratedColumn<String>(
      'variant_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _branchIdMeta =
      const VerificationMeta('branchId');
  @override
  late final GeneratedColumn<String> branchId = GeneratedColumn<String>(
      'branch_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _quantityMeta =
      const VerificationMeta('quantity');
  @override
  late final GeneratedColumn<int> quantity = GeneratedColumn<int>(
      'quantity', aliasedName, false,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(0));
  @override
  List<GeneratedColumn> get $columns => [variantId, branchId, quantity];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'variant_branch_stock';
  @override
  VerificationContext validateIntegrity(
      Insertable<VariantBranchStockTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('variant_id')) {
      context.handle(_variantIdMeta,
          variantId.isAcceptableOrUnknown(data['variant_id']!, _variantIdMeta));
    } else if (isInserting) {
      context.missing(_variantIdMeta);
    }
    if (data.containsKey('branch_id')) {
      context.handle(_branchIdMeta,
          branchId.isAcceptableOrUnknown(data['branch_id']!, _branchIdMeta));
    } else if (isInserting) {
      context.missing(_branchIdMeta);
    }
    if (data.containsKey('quantity')) {
      context.handle(_quantityMeta,
          quantity.isAcceptableOrUnknown(data['quantity']!, _quantityMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {variantId, branchId};
  @override
  VariantBranchStockTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return VariantBranchStockTableData(
      variantId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}variant_id'])!,
      branchId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}branch_id'])!,
      quantity: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}quantity'])!,
    );
  }

  @override
  $VariantBranchStockTableTable createAlias(String alias) {
    return $VariantBranchStockTableTable(attachedDatabase, alias);
  }
}

class VariantBranchStockTableData extends DataClass
    implements Insertable<VariantBranchStockTableData> {
  final String variantId;
  final String branchId;
  final int quantity;
  const VariantBranchStockTableData(
      {required this.variantId,
      required this.branchId,
      required this.quantity});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['variant_id'] = Variable<String>(variantId);
    map['branch_id'] = Variable<String>(branchId);
    map['quantity'] = Variable<int>(quantity);
    return map;
  }

  VariantBranchStockTableCompanion toCompanion(bool nullToAbsent) {
    return VariantBranchStockTableCompanion(
      variantId: Value(variantId),
      branchId: Value(branchId),
      quantity: Value(quantity),
    );
  }

  factory VariantBranchStockTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return VariantBranchStockTableData(
      variantId: serializer.fromJson<String>(json['variantId']),
      branchId: serializer.fromJson<String>(json['branchId']),
      quantity: serializer.fromJson<int>(json['quantity']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'variantId': serializer.toJson<String>(variantId),
      'branchId': serializer.toJson<String>(branchId),
      'quantity': serializer.toJson<int>(quantity),
    };
  }

  VariantBranchStockTableData copyWith(
          {String? variantId, String? branchId, int? quantity}) =>
      VariantBranchStockTableData(
        variantId: variantId ?? this.variantId,
        branchId: branchId ?? this.branchId,
        quantity: quantity ?? this.quantity,
      );
  VariantBranchStockTableData copyWithCompanion(
      VariantBranchStockTableCompanion data) {
    return VariantBranchStockTableData(
      variantId: data.variantId.present ? data.variantId.value : this.variantId,
      branchId: data.branchId.present ? data.branchId.value : this.branchId,
      quantity: data.quantity.present ? data.quantity.value : this.quantity,
    );
  }

  @override
  String toString() {
    return (StringBuffer('VariantBranchStockTableData(')
          ..write('variantId: $variantId, ')
          ..write('branchId: $branchId, ')
          ..write('quantity: $quantity')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(variantId, branchId, quantity);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is VariantBranchStockTableData &&
          other.variantId == this.variantId &&
          other.branchId == this.branchId &&
          other.quantity == this.quantity);
}

class VariantBranchStockTableCompanion
    extends UpdateCompanion<VariantBranchStockTableData> {
  final Value<String> variantId;
  final Value<String> branchId;
  final Value<int> quantity;
  final Value<int> rowid;
  const VariantBranchStockTableCompanion({
    this.variantId = const Value.absent(),
    this.branchId = const Value.absent(),
    this.quantity = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  VariantBranchStockTableCompanion.insert({
    required String variantId,
    required String branchId,
    this.quantity = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : variantId = Value(variantId),
        branchId = Value(branchId);
  static Insertable<VariantBranchStockTableData> custom({
    Expression<String>? variantId,
    Expression<String>? branchId,
    Expression<int>? quantity,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (variantId != null) 'variant_id': variantId,
      if (branchId != null) 'branch_id': branchId,
      if (quantity != null) 'quantity': quantity,
      if (rowid != null) 'rowid': rowid,
    });
  }

  VariantBranchStockTableCompanion copyWith(
      {Value<String>? variantId,
      Value<String>? branchId,
      Value<int>? quantity,
      Value<int>? rowid}) {
    return VariantBranchStockTableCompanion(
      variantId: variantId ?? this.variantId,
      branchId: branchId ?? this.branchId,
      quantity: quantity ?? this.quantity,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (variantId.present) {
      map['variant_id'] = Variable<String>(variantId.value);
    }
    if (branchId.present) {
      map['branch_id'] = Variable<String>(branchId.value);
    }
    if (quantity.present) {
      map['quantity'] = Variable<int>(quantity.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('VariantBranchStockTableCompanion(')
          ..write('variantId: $variantId, ')
          ..write('branchId: $branchId, ')
          ..write('quantity: $quantity, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $AddonGroupsTableTable extends AddonGroupsTable
    with TableInfo<$AddonGroupsTableTable, AddonGroupsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AddonGroupsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _productIdMeta =
      const VerificationMeta('productId');
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
      'product_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _selectionTypeMeta =
      const VerificationMeta('selectionType');
  @override
  late final GeneratedColumn<String> selectionType = GeneratedColumn<String>(
      'selection_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _minSelectMeta =
      const VerificationMeta('minSelect');
  @override
  late final GeneratedColumn<int> minSelect = GeneratedColumn<int>(
      'min_select', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _maxSelectMeta =
      const VerificationMeta('maxSelect');
  @override
  late final GeneratedColumn<int> maxSelect = GeneratedColumn<int>(
      'max_select', aliasedName, true,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _displayOrderMeta =
      const VerificationMeta('displayOrder');
  @override
  late final GeneratedColumn<int> displayOrder = GeneratedColumn<int>(
      'display_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns =>
      [id, productId, name, selectionType, minSelect, maxSelect, displayOrder];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'addon_groups';
  @override
  VerificationContext validateIntegrity(
      Insertable<AddonGroupsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('product_id')) {
      context.handle(_productIdMeta,
          productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta));
    } else if (isInserting) {
      context.missing(_productIdMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('selection_type')) {
      context.handle(
          _selectionTypeMeta,
          selectionType.isAcceptableOrUnknown(
              data['selection_type']!, _selectionTypeMeta));
    } else if (isInserting) {
      context.missing(_selectionTypeMeta);
    }
    if (data.containsKey('min_select')) {
      context.handle(_minSelectMeta,
          minSelect.isAcceptableOrUnknown(data['min_select']!, _minSelectMeta));
    } else if (isInserting) {
      context.missing(_minSelectMeta);
    }
    if (data.containsKey('max_select')) {
      context.handle(_maxSelectMeta,
          maxSelect.isAcceptableOrUnknown(data['max_select']!, _maxSelectMeta));
    }
    if (data.containsKey('display_order')) {
      context.handle(
          _displayOrderMeta,
          displayOrder.isAcceptableOrUnknown(
              data['display_order']!, _displayOrderMeta));
    } else if (isInserting) {
      context.missing(_displayOrderMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  AddonGroupsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AddonGroupsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      productId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      selectionType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}selection_type'])!,
      minSelect: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}min_select'])!,
      maxSelect: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}max_select']),
      displayOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}display_order'])!,
    );
  }

  @override
  $AddonGroupsTableTable createAlias(String alias) {
    return $AddonGroupsTableTable(attachedDatabase, alias);
  }
}

class AddonGroupsTableData extends DataClass
    implements Insertable<AddonGroupsTableData> {
  final String id;
  final String productId;
  final String name;
  final String selectionType;
  final int minSelect;
  final int? maxSelect;
  final int displayOrder;
  const AddonGroupsTableData(
      {required this.id,
      required this.productId,
      required this.name,
      required this.selectionType,
      required this.minSelect,
      this.maxSelect,
      required this.displayOrder});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['product_id'] = Variable<String>(productId);
    map['name'] = Variable<String>(name);
    map['selection_type'] = Variable<String>(selectionType);
    map['min_select'] = Variable<int>(minSelect);
    if (!nullToAbsent || maxSelect != null) {
      map['max_select'] = Variable<int>(maxSelect);
    }
    map['display_order'] = Variable<int>(displayOrder);
    return map;
  }

  AddonGroupsTableCompanion toCompanion(bool nullToAbsent) {
    return AddonGroupsTableCompanion(
      id: Value(id),
      productId: Value(productId),
      name: Value(name),
      selectionType: Value(selectionType),
      minSelect: Value(minSelect),
      maxSelect: maxSelect == null && nullToAbsent
          ? const Value.absent()
          : Value(maxSelect),
      displayOrder: Value(displayOrder),
    );
  }

  factory AddonGroupsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AddonGroupsTableData(
      id: serializer.fromJson<String>(json['id']),
      productId: serializer.fromJson<String>(json['productId']),
      name: serializer.fromJson<String>(json['name']),
      selectionType: serializer.fromJson<String>(json['selectionType']),
      minSelect: serializer.fromJson<int>(json['minSelect']),
      maxSelect: serializer.fromJson<int?>(json['maxSelect']),
      displayOrder: serializer.fromJson<int>(json['displayOrder']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'productId': serializer.toJson<String>(productId),
      'name': serializer.toJson<String>(name),
      'selectionType': serializer.toJson<String>(selectionType),
      'minSelect': serializer.toJson<int>(minSelect),
      'maxSelect': serializer.toJson<int?>(maxSelect),
      'displayOrder': serializer.toJson<int>(displayOrder),
    };
  }

  AddonGroupsTableData copyWith(
          {String? id,
          String? productId,
          String? name,
          String? selectionType,
          int? minSelect,
          Value<int?> maxSelect = const Value.absent(),
          int? displayOrder}) =>
      AddonGroupsTableData(
        id: id ?? this.id,
        productId: productId ?? this.productId,
        name: name ?? this.name,
        selectionType: selectionType ?? this.selectionType,
        minSelect: minSelect ?? this.minSelect,
        maxSelect: maxSelect.present ? maxSelect.value : this.maxSelect,
        displayOrder: displayOrder ?? this.displayOrder,
      );
  AddonGroupsTableData copyWithCompanion(AddonGroupsTableCompanion data) {
    return AddonGroupsTableData(
      id: data.id.present ? data.id.value : this.id,
      productId: data.productId.present ? data.productId.value : this.productId,
      name: data.name.present ? data.name.value : this.name,
      selectionType: data.selectionType.present
          ? data.selectionType.value
          : this.selectionType,
      minSelect: data.minSelect.present ? data.minSelect.value : this.minSelect,
      maxSelect: data.maxSelect.present ? data.maxSelect.value : this.maxSelect,
      displayOrder: data.displayOrder.present
          ? data.displayOrder.value
          : this.displayOrder,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AddonGroupsTableData(')
          ..write('id: $id, ')
          ..write('productId: $productId, ')
          ..write('name: $name, ')
          ..write('selectionType: $selectionType, ')
          ..write('minSelect: $minSelect, ')
          ..write('maxSelect: $maxSelect, ')
          ..write('displayOrder: $displayOrder')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, productId, name, selectionType, minSelect, maxSelect, displayOrder);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AddonGroupsTableData &&
          other.id == this.id &&
          other.productId == this.productId &&
          other.name == this.name &&
          other.selectionType == this.selectionType &&
          other.minSelect == this.minSelect &&
          other.maxSelect == this.maxSelect &&
          other.displayOrder == this.displayOrder);
}

class AddonGroupsTableCompanion extends UpdateCompanion<AddonGroupsTableData> {
  final Value<String> id;
  final Value<String> productId;
  final Value<String> name;
  final Value<String> selectionType;
  final Value<int> minSelect;
  final Value<int?> maxSelect;
  final Value<int> displayOrder;
  final Value<int> rowid;
  const AddonGroupsTableCompanion({
    this.id = const Value.absent(),
    this.productId = const Value.absent(),
    this.name = const Value.absent(),
    this.selectionType = const Value.absent(),
    this.minSelect = const Value.absent(),
    this.maxSelect = const Value.absent(),
    this.displayOrder = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AddonGroupsTableCompanion.insert({
    required String id,
    required String productId,
    required String name,
    required String selectionType,
    required int minSelect,
    this.maxSelect = const Value.absent(),
    required int displayOrder,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        productId = Value(productId),
        name = Value(name),
        selectionType = Value(selectionType),
        minSelect = Value(minSelect),
        displayOrder = Value(displayOrder);
  static Insertable<AddonGroupsTableData> custom({
    Expression<String>? id,
    Expression<String>? productId,
    Expression<String>? name,
    Expression<String>? selectionType,
    Expression<int>? minSelect,
    Expression<int>? maxSelect,
    Expression<int>? displayOrder,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (productId != null) 'product_id': productId,
      if (name != null) 'name': name,
      if (selectionType != null) 'selection_type': selectionType,
      if (minSelect != null) 'min_select': minSelect,
      if (maxSelect != null) 'max_select': maxSelect,
      if (displayOrder != null) 'display_order': displayOrder,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AddonGroupsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? productId,
      Value<String>? name,
      Value<String>? selectionType,
      Value<int>? minSelect,
      Value<int?>? maxSelect,
      Value<int>? displayOrder,
      Value<int>? rowid}) {
    return AddonGroupsTableCompanion(
      id: id ?? this.id,
      productId: productId ?? this.productId,
      name: name ?? this.name,
      selectionType: selectionType ?? this.selectionType,
      minSelect: minSelect ?? this.minSelect,
      maxSelect: maxSelect ?? this.maxSelect,
      displayOrder: displayOrder ?? this.displayOrder,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (selectionType.present) {
      map['selection_type'] = Variable<String>(selectionType.value);
    }
    if (minSelect.present) {
      map['min_select'] = Variable<int>(minSelect.value);
    }
    if (maxSelect.present) {
      map['max_select'] = Variable<int>(maxSelect.value);
    }
    if (displayOrder.present) {
      map['display_order'] = Variable<int>(displayOrder.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AddonGroupsTableCompanion(')
          ..write('id: $id, ')
          ..write('productId: $productId, ')
          ..write('name: $name, ')
          ..write('selectionType: $selectionType, ')
          ..write('minSelect: $minSelect, ')
          ..write('maxSelect: $maxSelect, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $AddonItemsTableTable extends AddonItemsTable
    with TableInfo<$AddonItemsTableTable, AddonItemsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AddonItemsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _addonGroupIdMeta =
      const VerificationMeta('addonGroupId');
  @override
  late final GeneratedColumn<String> addonGroupId = GeneratedColumn<String>(
      'addon_group_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _priceDeltaMeta =
      const VerificationMeta('priceDelta');
  @override
  late final GeneratedColumn<String> priceDelta = GeneratedColumn<String>(
      'price_delta', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _defaultSelectedMeta =
      const VerificationMeta('defaultSelected');
  @override
  late final GeneratedColumn<bool> defaultSelected = GeneratedColumn<bool>(
      'default_selected', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("default_selected" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _displayOrderMeta =
      const VerificationMeta('displayOrder');
  @override
  late final GeneratedColumn<int> displayOrder = GeneratedColumn<int>(
      'display_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _isActiveMeta =
      const VerificationMeta('isActive');
  @override
  late final GeneratedColumn<bool> isActive = GeneratedColumn<bool>(
      'is_active', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_active" IN (0, 1))'));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        addonGroupId,
        name,
        priceDelta,
        defaultSelected,
        displayOrder,
        isActive
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'addon_items';
  @override
  VerificationContext validateIntegrity(
      Insertable<AddonItemsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('addon_group_id')) {
      context.handle(
          _addonGroupIdMeta,
          addonGroupId.isAcceptableOrUnknown(
              data['addon_group_id']!, _addonGroupIdMeta));
    } else if (isInserting) {
      context.missing(_addonGroupIdMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('price_delta')) {
      context.handle(
          _priceDeltaMeta,
          priceDelta.isAcceptableOrUnknown(
              data['price_delta']!, _priceDeltaMeta));
    } else if (isInserting) {
      context.missing(_priceDeltaMeta);
    }
    if (data.containsKey('default_selected')) {
      context.handle(
          _defaultSelectedMeta,
          defaultSelected.isAcceptableOrUnknown(
              data['default_selected']!, _defaultSelectedMeta));
    }
    if (data.containsKey('display_order')) {
      context.handle(
          _displayOrderMeta,
          displayOrder.isAcceptableOrUnknown(
              data['display_order']!, _displayOrderMeta));
    } else if (isInserting) {
      context.missing(_displayOrderMeta);
    }
    if (data.containsKey('is_active')) {
      context.handle(_isActiveMeta,
          isActive.isAcceptableOrUnknown(data['is_active']!, _isActiveMeta));
    } else if (isInserting) {
      context.missing(_isActiveMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  AddonItemsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AddonItemsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      addonGroupId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}addon_group_id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      priceDelta: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}price_delta'])!,
      defaultSelected: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}default_selected'])!,
      displayOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}display_order'])!,
      isActive: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_active'])!,
    );
  }

  @override
  $AddonItemsTableTable createAlias(String alias) {
    return $AddonItemsTableTable(attachedDatabase, alias);
  }
}

class AddonItemsTableData extends DataClass
    implements Insertable<AddonItemsTableData> {
  final String id;
  final String addonGroupId;
  final String name;
  final String priceDelta;
  final bool defaultSelected;
  final int displayOrder;
  final bool isActive;
  const AddonItemsTableData(
      {required this.id,
      required this.addonGroupId,
      required this.name,
      required this.priceDelta,
      required this.defaultSelected,
      required this.displayOrder,
      required this.isActive});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['addon_group_id'] = Variable<String>(addonGroupId);
    map['name'] = Variable<String>(name);
    map['price_delta'] = Variable<String>(priceDelta);
    map['default_selected'] = Variable<bool>(defaultSelected);
    map['display_order'] = Variable<int>(displayOrder);
    map['is_active'] = Variable<bool>(isActive);
    return map;
  }

  AddonItemsTableCompanion toCompanion(bool nullToAbsent) {
    return AddonItemsTableCompanion(
      id: Value(id),
      addonGroupId: Value(addonGroupId),
      name: Value(name),
      priceDelta: Value(priceDelta),
      defaultSelected: Value(defaultSelected),
      displayOrder: Value(displayOrder),
      isActive: Value(isActive),
    );
  }

  factory AddonItemsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AddonItemsTableData(
      id: serializer.fromJson<String>(json['id']),
      addonGroupId: serializer.fromJson<String>(json['addonGroupId']),
      name: serializer.fromJson<String>(json['name']),
      priceDelta: serializer.fromJson<String>(json['priceDelta']),
      defaultSelected: serializer.fromJson<bool>(json['defaultSelected']),
      displayOrder: serializer.fromJson<int>(json['displayOrder']),
      isActive: serializer.fromJson<bool>(json['isActive']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'addonGroupId': serializer.toJson<String>(addonGroupId),
      'name': serializer.toJson<String>(name),
      'priceDelta': serializer.toJson<String>(priceDelta),
      'defaultSelected': serializer.toJson<bool>(defaultSelected),
      'displayOrder': serializer.toJson<int>(displayOrder),
      'isActive': serializer.toJson<bool>(isActive),
    };
  }

  AddonItemsTableData copyWith(
          {String? id,
          String? addonGroupId,
          String? name,
          String? priceDelta,
          bool? defaultSelected,
          int? displayOrder,
          bool? isActive}) =>
      AddonItemsTableData(
        id: id ?? this.id,
        addonGroupId: addonGroupId ?? this.addonGroupId,
        name: name ?? this.name,
        priceDelta: priceDelta ?? this.priceDelta,
        defaultSelected: defaultSelected ?? this.defaultSelected,
        displayOrder: displayOrder ?? this.displayOrder,
        isActive: isActive ?? this.isActive,
      );
  AddonItemsTableData copyWithCompanion(AddonItemsTableCompanion data) {
    return AddonItemsTableData(
      id: data.id.present ? data.id.value : this.id,
      addonGroupId: data.addonGroupId.present
          ? data.addonGroupId.value
          : this.addonGroupId,
      name: data.name.present ? data.name.value : this.name,
      priceDelta:
          data.priceDelta.present ? data.priceDelta.value : this.priceDelta,
      defaultSelected: data.defaultSelected.present
          ? data.defaultSelected.value
          : this.defaultSelected,
      displayOrder: data.displayOrder.present
          ? data.displayOrder.value
          : this.displayOrder,
      isActive: data.isActive.present ? data.isActive.value : this.isActive,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AddonItemsTableData(')
          ..write('id: $id, ')
          ..write('addonGroupId: $addonGroupId, ')
          ..write('name: $name, ')
          ..write('priceDelta: $priceDelta, ')
          ..write('defaultSelected: $defaultSelected, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, addonGroupId, name, priceDelta,
      defaultSelected, displayOrder, isActive);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AddonItemsTableData &&
          other.id == this.id &&
          other.addonGroupId == this.addonGroupId &&
          other.name == this.name &&
          other.priceDelta == this.priceDelta &&
          other.defaultSelected == this.defaultSelected &&
          other.displayOrder == this.displayOrder &&
          other.isActive == this.isActive);
}

class AddonItemsTableCompanion extends UpdateCompanion<AddonItemsTableData> {
  final Value<String> id;
  final Value<String> addonGroupId;
  final Value<String> name;
  final Value<String> priceDelta;
  final Value<bool> defaultSelected;
  final Value<int> displayOrder;
  final Value<bool> isActive;
  final Value<int> rowid;
  const AddonItemsTableCompanion({
    this.id = const Value.absent(),
    this.addonGroupId = const Value.absent(),
    this.name = const Value.absent(),
    this.priceDelta = const Value.absent(),
    this.defaultSelected = const Value.absent(),
    this.displayOrder = const Value.absent(),
    this.isActive = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AddonItemsTableCompanion.insert({
    required String id,
    required String addonGroupId,
    required String name,
    required String priceDelta,
    this.defaultSelected = const Value.absent(),
    required int displayOrder,
    required bool isActive,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        addonGroupId = Value(addonGroupId),
        name = Value(name),
        priceDelta = Value(priceDelta),
        displayOrder = Value(displayOrder),
        isActive = Value(isActive);
  static Insertable<AddonItemsTableData> custom({
    Expression<String>? id,
    Expression<String>? addonGroupId,
    Expression<String>? name,
    Expression<String>? priceDelta,
    Expression<bool>? defaultSelected,
    Expression<int>? displayOrder,
    Expression<bool>? isActive,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (addonGroupId != null) 'addon_group_id': addonGroupId,
      if (name != null) 'name': name,
      if (priceDelta != null) 'price_delta': priceDelta,
      if (defaultSelected != null) 'default_selected': defaultSelected,
      if (displayOrder != null) 'display_order': displayOrder,
      if (isActive != null) 'is_active': isActive,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AddonItemsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? addonGroupId,
      Value<String>? name,
      Value<String>? priceDelta,
      Value<bool>? defaultSelected,
      Value<int>? displayOrder,
      Value<bool>? isActive,
      Value<int>? rowid}) {
    return AddonItemsTableCompanion(
      id: id ?? this.id,
      addonGroupId: addonGroupId ?? this.addonGroupId,
      name: name ?? this.name,
      priceDelta: priceDelta ?? this.priceDelta,
      defaultSelected: defaultSelected ?? this.defaultSelected,
      displayOrder: displayOrder ?? this.displayOrder,
      isActive: isActive ?? this.isActive,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (addonGroupId.present) {
      map['addon_group_id'] = Variable<String>(addonGroupId.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (priceDelta.present) {
      map['price_delta'] = Variable<String>(priceDelta.value);
    }
    if (defaultSelected.present) {
      map['default_selected'] = Variable<bool>(defaultSelected.value);
    }
    if (displayOrder.present) {
      map['display_order'] = Variable<int>(displayOrder.value);
    }
    if (isActive.present) {
      map['is_active'] = Variable<bool>(isActive.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AddonItemsTableCompanion(')
          ..write('id: $id, ')
          ..write('addonGroupId: $addonGroupId, ')
          ..write('name: $name, ')
          ..write('priceDelta: $priceDelta, ')
          ..write('defaultSelected: $defaultSelected, ')
          ..write('displayOrder: $displayOrder, ')
          ..write('isActive: $isActive, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $TaxRatesTableTable extends TaxRatesTable
    with TableInfo<$TaxRatesTableTable, TaxRatesTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $TaxRatesTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _rateMeta = const VerificationMeta('rate');
  @override
  late final GeneratedColumn<String> rate = GeneratedColumn<String>(
      'rate', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _isInclusiveMeta =
      const VerificationMeta('isInclusive');
  @override
  late final GeneratedColumn<bool> isInclusive = GeneratedColumn<bool>(
      'is_inclusive', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("is_inclusive" IN (0, 1))'));
  static const VerificationMeta _isDefaultMeta =
      const VerificationMeta('isDefault');
  @override
  late final GeneratedColumn<bool> isDefault = GeneratedColumn<bool>(
      'is_default', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_default" IN (0, 1))'));
  @override
  List<GeneratedColumn> get $columns =>
      [id, name, rate, isInclusive, isDefault];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'tax_rates';
  @override
  VerificationContext validateIntegrity(Insertable<TaxRatesTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('rate')) {
      context.handle(
          _rateMeta, rate.isAcceptableOrUnknown(data['rate']!, _rateMeta));
    } else if (isInserting) {
      context.missing(_rateMeta);
    }
    if (data.containsKey('is_inclusive')) {
      context.handle(
          _isInclusiveMeta,
          isInclusive.isAcceptableOrUnknown(
              data['is_inclusive']!, _isInclusiveMeta));
    } else if (isInserting) {
      context.missing(_isInclusiveMeta);
    }
    if (data.containsKey('is_default')) {
      context.handle(_isDefaultMeta,
          isDefault.isAcceptableOrUnknown(data['is_default']!, _isDefaultMeta));
    } else if (isInserting) {
      context.missing(_isDefaultMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  TaxRatesTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return TaxRatesTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      rate: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}rate'])!,
      isInclusive: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_inclusive'])!,
      isDefault: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_default'])!,
    );
  }

  @override
  $TaxRatesTableTable createAlias(String alias) {
    return $TaxRatesTableTable(attachedDatabase, alias);
  }
}

class TaxRatesTableData extends DataClass
    implements Insertable<TaxRatesTableData> {
  final String id;
  final String name;

  /// Decimal rate value stored as TEXT, e.g. "0.10" for 10%.
  final String rate;

  /// True when the tax is already included in product prices (no extra charge at checkout).
  final bool isInclusive;
  final bool isDefault;
  const TaxRatesTableData(
      {required this.id,
      required this.name,
      required this.rate,
      required this.isInclusive,
      required this.isDefault});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    map['rate'] = Variable<String>(rate);
    map['is_inclusive'] = Variable<bool>(isInclusive);
    map['is_default'] = Variable<bool>(isDefault);
    return map;
  }

  TaxRatesTableCompanion toCompanion(bool nullToAbsent) {
    return TaxRatesTableCompanion(
      id: Value(id),
      name: Value(name),
      rate: Value(rate),
      isInclusive: Value(isInclusive),
      isDefault: Value(isDefault),
    );
  }

  factory TaxRatesTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return TaxRatesTableData(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      rate: serializer.fromJson<String>(json['rate']),
      isInclusive: serializer.fromJson<bool>(json['isInclusive']),
      isDefault: serializer.fromJson<bool>(json['isDefault']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'rate': serializer.toJson<String>(rate),
      'isInclusive': serializer.toJson<bool>(isInclusive),
      'isDefault': serializer.toJson<bool>(isDefault),
    };
  }

  TaxRatesTableData copyWith(
          {String? id,
          String? name,
          String? rate,
          bool? isInclusive,
          bool? isDefault}) =>
      TaxRatesTableData(
        id: id ?? this.id,
        name: name ?? this.name,
        rate: rate ?? this.rate,
        isInclusive: isInclusive ?? this.isInclusive,
        isDefault: isDefault ?? this.isDefault,
      );
  TaxRatesTableData copyWithCompanion(TaxRatesTableCompanion data) {
    return TaxRatesTableData(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      rate: data.rate.present ? data.rate.value : this.rate,
      isInclusive:
          data.isInclusive.present ? data.isInclusive.value : this.isInclusive,
      isDefault: data.isDefault.present ? data.isDefault.value : this.isDefault,
    );
  }

  @override
  String toString() {
    return (StringBuffer('TaxRatesTableData(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('rate: $rate, ')
          ..write('isInclusive: $isInclusive, ')
          ..write('isDefault: $isDefault')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, name, rate, isInclusive, isDefault);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is TaxRatesTableData &&
          other.id == this.id &&
          other.name == this.name &&
          other.rate == this.rate &&
          other.isInclusive == this.isInclusive &&
          other.isDefault == this.isDefault);
}

class TaxRatesTableCompanion extends UpdateCompanion<TaxRatesTableData> {
  final Value<String> id;
  final Value<String> name;
  final Value<String> rate;
  final Value<bool> isInclusive;
  final Value<bool> isDefault;
  final Value<int> rowid;
  const TaxRatesTableCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.rate = const Value.absent(),
    this.isInclusive = const Value.absent(),
    this.isDefault = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  TaxRatesTableCompanion.insert({
    required String id,
    required String name,
    required String rate,
    required bool isInclusive,
    required bool isDefault,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        name = Value(name),
        rate = Value(rate),
        isInclusive = Value(isInclusive),
        isDefault = Value(isDefault);
  static Insertable<TaxRatesTableData> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? rate,
    Expression<bool>? isInclusive,
    Expression<bool>? isDefault,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (rate != null) 'rate': rate,
      if (isInclusive != null) 'is_inclusive': isInclusive,
      if (isDefault != null) 'is_default': isDefault,
      if (rowid != null) 'rowid': rowid,
    });
  }

  TaxRatesTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? name,
      Value<String>? rate,
      Value<bool>? isInclusive,
      Value<bool>? isDefault,
      Value<int>? rowid}) {
    return TaxRatesTableCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      rate: rate ?? this.rate,
      isInclusive: isInclusive ?? this.isInclusive,
      isDefault: isDefault ?? this.isDefault,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (rate.present) {
      map['rate'] = Variable<String>(rate.value);
    }
    if (isInclusive.present) {
      map['is_inclusive'] = Variable<bool>(isInclusive.value);
    }
    if (isDefault.present) {
      map['is_default'] = Variable<bool>(isDefault.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('TaxRatesTableCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('rate: $rate, ')
          ..write('isInclusive: $isInclusive, ')
          ..write('isDefault: $isDefault, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $DealsTableTable extends DealsTable
    with TableInfo<$DealsTableTable, DealsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $DealsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _dealCodeMeta =
      const VerificationMeta('dealCode');
  @override
  late final GeneratedColumn<String> dealCode = GeneratedColumn<String>(
      'deal_code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _fixedPriceMeta =
      const VerificationMeta('fixedPrice');
  @override
  late final GeneratedColumn<String> fixedPrice = GeneratedColumn<String>(
      'fixed_price', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _discountValueMeta =
      const VerificationMeta('discountValue');
  @override
  late final GeneratedColumn<String> discountValue = GeneratedColumn<String>(
      'discount_value', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _discountTypeMeta =
      const VerificationMeta('discountType');
  @override
  late final GeneratedColumn<String> discountType = GeneratedColumn<String>(
      'discount_type', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _validFromMeta =
      const VerificationMeta('validFrom');
  @override
  late final GeneratedColumn<DateTime> validFrom = GeneratedColumn<DateTime>(
      'valid_from', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _validUntilMeta =
      const VerificationMeta('validUntil');
  @override
  late final GeneratedColumn<DateTime> validUntil = GeneratedColumn<DateTime>(
      'valid_until', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _isActiveMeta =
      const VerificationMeta('isActive');
  @override
  late final GeneratedColumn<bool> isActive = GeneratedColumn<bool>(
      'is_active', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_active" IN (0, 1))'));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        name,
        description,
        dealCode,
        fixedPrice,
        discountValue,
        discountType,
        validFrom,
        validUntil,
        isActive
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'deals';
  @override
  VerificationContext validateIntegrity(Insertable<DealsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    }
    if (data.containsKey('deal_code')) {
      context.handle(_dealCodeMeta,
          dealCode.isAcceptableOrUnknown(data['deal_code']!, _dealCodeMeta));
    } else if (isInserting) {
      context.missing(_dealCodeMeta);
    }
    if (data.containsKey('fixed_price')) {
      context.handle(
          _fixedPriceMeta,
          fixedPrice.isAcceptableOrUnknown(
              data['fixed_price']!, _fixedPriceMeta));
    }
    if (data.containsKey('discount_value')) {
      context.handle(
          _discountValueMeta,
          discountValue.isAcceptableOrUnknown(
              data['discount_value']!, _discountValueMeta));
    }
    if (data.containsKey('discount_type')) {
      context.handle(
          _discountTypeMeta,
          discountType.isAcceptableOrUnknown(
              data['discount_type']!, _discountTypeMeta));
    }
    if (data.containsKey('valid_from')) {
      context.handle(_validFromMeta,
          validFrom.isAcceptableOrUnknown(data['valid_from']!, _validFromMeta));
    }
    if (data.containsKey('valid_until')) {
      context.handle(
          _validUntilMeta,
          validUntil.isAcceptableOrUnknown(
              data['valid_until']!, _validUntilMeta));
    }
    if (data.containsKey('is_active')) {
      context.handle(_isActiveMeta,
          isActive.isAcceptableOrUnknown(data['is_active']!, _isActiveMeta));
    } else if (isInserting) {
      context.missing(_isActiveMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  DealsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return DealsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description']),
      dealCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}deal_code'])!,
      fixedPrice: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}fixed_price']),
      discountValue: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}discount_value']),
      discountType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}discount_type']),
      validFrom: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}valid_from']),
      validUntil: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}valid_until']),
      isActive: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_active'])!,
    );
  }

  @override
  $DealsTableTable createAlias(String alias) {
    return $DealsTableTable(attachedDatabase, alias);
  }
}

class DealsTableData extends DataClass implements Insertable<DealsTableData> {
  final String id;
  final String name;
  final String? description;
  final String dealCode;

  /// Fixed bundle price as TEXT (Decimal); null when discount-based pricing is used.
  final String? fixedPrice;

  /// Discount magnitude as TEXT (Decimal); interpreted alongside [discountType].
  final String? discountValue;

  /// "flat" or "percent" — how [discountValue] is applied.
  final String? discountType;
  final DateTime? validFrom;
  final DateTime? validUntil;
  final bool isActive;
  const DealsTableData(
      {required this.id,
      required this.name,
      this.description,
      required this.dealCode,
      this.fixedPrice,
      this.discountValue,
      this.discountType,
      this.validFrom,
      this.validUntil,
      required this.isActive});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    map['deal_code'] = Variable<String>(dealCode);
    if (!nullToAbsent || fixedPrice != null) {
      map['fixed_price'] = Variable<String>(fixedPrice);
    }
    if (!nullToAbsent || discountValue != null) {
      map['discount_value'] = Variable<String>(discountValue);
    }
    if (!nullToAbsent || discountType != null) {
      map['discount_type'] = Variable<String>(discountType);
    }
    if (!nullToAbsent || validFrom != null) {
      map['valid_from'] = Variable<DateTime>(validFrom);
    }
    if (!nullToAbsent || validUntil != null) {
      map['valid_until'] = Variable<DateTime>(validUntil);
    }
    map['is_active'] = Variable<bool>(isActive);
    return map;
  }

  DealsTableCompanion toCompanion(bool nullToAbsent) {
    return DealsTableCompanion(
      id: Value(id),
      name: Value(name),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      dealCode: Value(dealCode),
      fixedPrice: fixedPrice == null && nullToAbsent
          ? const Value.absent()
          : Value(fixedPrice),
      discountValue: discountValue == null && nullToAbsent
          ? const Value.absent()
          : Value(discountValue),
      discountType: discountType == null && nullToAbsent
          ? const Value.absent()
          : Value(discountType),
      validFrom: validFrom == null && nullToAbsent
          ? const Value.absent()
          : Value(validFrom),
      validUntil: validUntil == null && nullToAbsent
          ? const Value.absent()
          : Value(validUntil),
      isActive: Value(isActive),
    );
  }

  factory DealsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return DealsTableData(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      description: serializer.fromJson<String?>(json['description']),
      dealCode: serializer.fromJson<String>(json['dealCode']),
      fixedPrice: serializer.fromJson<String?>(json['fixedPrice']),
      discountValue: serializer.fromJson<String?>(json['discountValue']),
      discountType: serializer.fromJson<String?>(json['discountType']),
      validFrom: serializer.fromJson<DateTime?>(json['validFrom']),
      validUntil: serializer.fromJson<DateTime?>(json['validUntil']),
      isActive: serializer.fromJson<bool>(json['isActive']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'description': serializer.toJson<String?>(description),
      'dealCode': serializer.toJson<String>(dealCode),
      'fixedPrice': serializer.toJson<String?>(fixedPrice),
      'discountValue': serializer.toJson<String?>(discountValue),
      'discountType': serializer.toJson<String?>(discountType),
      'validFrom': serializer.toJson<DateTime?>(validFrom),
      'validUntil': serializer.toJson<DateTime?>(validUntil),
      'isActive': serializer.toJson<bool>(isActive),
    };
  }

  DealsTableData copyWith(
          {String? id,
          String? name,
          Value<String?> description = const Value.absent(),
          String? dealCode,
          Value<String?> fixedPrice = const Value.absent(),
          Value<String?> discountValue = const Value.absent(),
          Value<String?> discountType = const Value.absent(),
          Value<DateTime?> validFrom = const Value.absent(),
          Value<DateTime?> validUntil = const Value.absent(),
          bool? isActive}) =>
      DealsTableData(
        id: id ?? this.id,
        name: name ?? this.name,
        description: description.present ? description.value : this.description,
        dealCode: dealCode ?? this.dealCode,
        fixedPrice: fixedPrice.present ? fixedPrice.value : this.fixedPrice,
        discountValue:
            discountValue.present ? discountValue.value : this.discountValue,
        discountType:
            discountType.present ? discountType.value : this.discountType,
        validFrom: validFrom.present ? validFrom.value : this.validFrom,
        validUntil: validUntil.present ? validUntil.value : this.validUntil,
        isActive: isActive ?? this.isActive,
      );
  DealsTableData copyWithCompanion(DealsTableCompanion data) {
    return DealsTableData(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      description:
          data.description.present ? data.description.value : this.description,
      dealCode: data.dealCode.present ? data.dealCode.value : this.dealCode,
      fixedPrice:
          data.fixedPrice.present ? data.fixedPrice.value : this.fixedPrice,
      discountValue: data.discountValue.present
          ? data.discountValue.value
          : this.discountValue,
      discountType: data.discountType.present
          ? data.discountType.value
          : this.discountType,
      validFrom: data.validFrom.present ? data.validFrom.value : this.validFrom,
      validUntil:
          data.validUntil.present ? data.validUntil.value : this.validUntil,
      isActive: data.isActive.present ? data.isActive.value : this.isActive,
    );
  }

  @override
  String toString() {
    return (StringBuffer('DealsTableData(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('dealCode: $dealCode, ')
          ..write('fixedPrice: $fixedPrice, ')
          ..write('discountValue: $discountValue, ')
          ..write('discountType: $discountType, ')
          ..write('validFrom: $validFrom, ')
          ..write('validUntil: $validUntil, ')
          ..write('isActive: $isActive')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, name, description, dealCode, fixedPrice,
      discountValue, discountType, validFrom, validUntil, isActive);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is DealsTableData &&
          other.id == this.id &&
          other.name == this.name &&
          other.description == this.description &&
          other.dealCode == this.dealCode &&
          other.fixedPrice == this.fixedPrice &&
          other.discountValue == this.discountValue &&
          other.discountType == this.discountType &&
          other.validFrom == this.validFrom &&
          other.validUntil == this.validUntil &&
          other.isActive == this.isActive);
}

class DealsTableCompanion extends UpdateCompanion<DealsTableData> {
  final Value<String> id;
  final Value<String> name;
  final Value<String?> description;
  final Value<String> dealCode;
  final Value<String?> fixedPrice;
  final Value<String?> discountValue;
  final Value<String?> discountType;
  final Value<DateTime?> validFrom;
  final Value<DateTime?> validUntil;
  final Value<bool> isActive;
  final Value<int> rowid;
  const DealsTableCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.description = const Value.absent(),
    this.dealCode = const Value.absent(),
    this.fixedPrice = const Value.absent(),
    this.discountValue = const Value.absent(),
    this.discountType = const Value.absent(),
    this.validFrom = const Value.absent(),
    this.validUntil = const Value.absent(),
    this.isActive = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  DealsTableCompanion.insert({
    required String id,
    required String name,
    this.description = const Value.absent(),
    required String dealCode,
    this.fixedPrice = const Value.absent(),
    this.discountValue = const Value.absent(),
    this.discountType = const Value.absent(),
    this.validFrom = const Value.absent(),
    this.validUntil = const Value.absent(),
    required bool isActive,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        name = Value(name),
        dealCode = Value(dealCode),
        isActive = Value(isActive);
  static Insertable<DealsTableData> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? description,
    Expression<String>? dealCode,
    Expression<String>? fixedPrice,
    Expression<String>? discountValue,
    Expression<String>? discountType,
    Expression<DateTime>? validFrom,
    Expression<DateTime>? validUntil,
    Expression<bool>? isActive,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (description != null) 'description': description,
      if (dealCode != null) 'deal_code': dealCode,
      if (fixedPrice != null) 'fixed_price': fixedPrice,
      if (discountValue != null) 'discount_value': discountValue,
      if (discountType != null) 'discount_type': discountType,
      if (validFrom != null) 'valid_from': validFrom,
      if (validUntil != null) 'valid_until': validUntil,
      if (isActive != null) 'is_active': isActive,
      if (rowid != null) 'rowid': rowid,
    });
  }

  DealsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? name,
      Value<String?>? description,
      Value<String>? dealCode,
      Value<String?>? fixedPrice,
      Value<String?>? discountValue,
      Value<String?>? discountType,
      Value<DateTime?>? validFrom,
      Value<DateTime?>? validUntil,
      Value<bool>? isActive,
      Value<int>? rowid}) {
    return DealsTableCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      dealCode: dealCode ?? this.dealCode,
      fixedPrice: fixedPrice ?? this.fixedPrice,
      discountValue: discountValue ?? this.discountValue,
      discountType: discountType ?? this.discountType,
      validFrom: validFrom ?? this.validFrom,
      validUntil: validUntil ?? this.validUntil,
      isActive: isActive ?? this.isActive,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (dealCode.present) {
      map['deal_code'] = Variable<String>(dealCode.value);
    }
    if (fixedPrice.present) {
      map['fixed_price'] = Variable<String>(fixedPrice.value);
    }
    if (discountValue.present) {
      map['discount_value'] = Variable<String>(discountValue.value);
    }
    if (discountType.present) {
      map['discount_type'] = Variable<String>(discountType.value);
    }
    if (validFrom.present) {
      map['valid_from'] = Variable<DateTime>(validFrom.value);
    }
    if (validUntil.present) {
      map['valid_until'] = Variable<DateTime>(validUntil.value);
    }
    if (isActive.present) {
      map['is_active'] = Variable<bool>(isActive.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('DealsTableCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('dealCode: $dealCode, ')
          ..write('fixedPrice: $fixedPrice, ')
          ..write('discountValue: $discountValue, ')
          ..write('discountType: $discountType, ')
          ..write('validFrom: $validFrom, ')
          ..write('validUntil: $validUntil, ')
          ..write('isActive: $isActive, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $DealItemsTableTable extends DealItemsTable
    with TableInfo<$DealItemsTableTable, DealItemsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $DealItemsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _dealIdMeta = const VerificationMeta('dealId');
  @override
  late final GeneratedColumn<String> dealId = GeneratedColumn<String>(
      'deal_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _productIdMeta =
      const VerificationMeta('productId');
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
      'product_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _categoryIdMeta =
      const VerificationMeta('categoryId');
  @override
  late final GeneratedColumn<String> categoryId = GeneratedColumn<String>(
      'category_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _quantityMeta =
      const VerificationMeta('quantity');
  @override
  late final GeneratedColumn<int> quantity = GeneratedColumn<int>(
      'quantity', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _isFreeMeta = const VerificationMeta('isFree');
  @override
  late final GeneratedColumn<bool> isFree = GeneratedColumn<bool>(
      'is_free', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_free" IN (0, 1))'));
  static const VerificationMeta _sortOrderMeta =
      const VerificationMeta('sortOrder');
  @override
  late final GeneratedColumn<int> sortOrder = GeneratedColumn<int>(
      'sort_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns =>
      [id, dealId, productId, categoryId, quantity, isFree, sortOrder];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'deal_items';
  @override
  VerificationContext validateIntegrity(Insertable<DealItemsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('deal_id')) {
      context.handle(_dealIdMeta,
          dealId.isAcceptableOrUnknown(data['deal_id']!, _dealIdMeta));
    } else if (isInserting) {
      context.missing(_dealIdMeta);
    }
    if (data.containsKey('product_id')) {
      context.handle(_productIdMeta,
          productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta));
    }
    if (data.containsKey('category_id')) {
      context.handle(
          _categoryIdMeta,
          categoryId.isAcceptableOrUnknown(
              data['category_id']!, _categoryIdMeta));
    }
    if (data.containsKey('quantity')) {
      context.handle(_quantityMeta,
          quantity.isAcceptableOrUnknown(data['quantity']!, _quantityMeta));
    } else if (isInserting) {
      context.missing(_quantityMeta);
    }
    if (data.containsKey('is_free')) {
      context.handle(_isFreeMeta,
          isFree.isAcceptableOrUnknown(data['is_free']!, _isFreeMeta));
    } else if (isInserting) {
      context.missing(_isFreeMeta);
    }
    if (data.containsKey('sort_order')) {
      context.handle(_sortOrderMeta,
          sortOrder.isAcceptableOrUnknown(data['sort_order']!, _sortOrderMeta));
    } else if (isInserting) {
      context.missing(_sortOrderMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  DealItemsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return DealItemsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      dealId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}deal_id'])!,
      productId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_id']),
      categoryId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}category_id']),
      quantity: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}quantity'])!,
      isFree: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_free'])!,
      sortOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}sort_order'])!,
    );
  }

  @override
  $DealItemsTableTable createAlias(String alias) {
    return $DealItemsTableTable(attachedDatabase, alias);
  }
}

class DealItemsTableData extends DataClass
    implements Insertable<DealItemsTableData> {
  final String id;
  final String dealId;

  /// Specific product for this slot; null when any product in [categoryId] qualifies.
  final String? productId;

  /// Category constraint; null when a specific [productId] is required.
  final String? categoryId;
  final int quantity;
  final bool isFree;
  final int sortOrder;
  const DealItemsTableData(
      {required this.id,
      required this.dealId,
      this.productId,
      this.categoryId,
      required this.quantity,
      required this.isFree,
      required this.sortOrder});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['deal_id'] = Variable<String>(dealId);
    if (!nullToAbsent || productId != null) {
      map['product_id'] = Variable<String>(productId);
    }
    if (!nullToAbsent || categoryId != null) {
      map['category_id'] = Variable<String>(categoryId);
    }
    map['quantity'] = Variable<int>(quantity);
    map['is_free'] = Variable<bool>(isFree);
    map['sort_order'] = Variable<int>(sortOrder);
    return map;
  }

  DealItemsTableCompanion toCompanion(bool nullToAbsent) {
    return DealItemsTableCompanion(
      id: Value(id),
      dealId: Value(dealId),
      productId: productId == null && nullToAbsent
          ? const Value.absent()
          : Value(productId),
      categoryId: categoryId == null && nullToAbsent
          ? const Value.absent()
          : Value(categoryId),
      quantity: Value(quantity),
      isFree: Value(isFree),
      sortOrder: Value(sortOrder),
    );
  }

  factory DealItemsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return DealItemsTableData(
      id: serializer.fromJson<String>(json['id']),
      dealId: serializer.fromJson<String>(json['dealId']),
      productId: serializer.fromJson<String?>(json['productId']),
      categoryId: serializer.fromJson<String?>(json['categoryId']),
      quantity: serializer.fromJson<int>(json['quantity']),
      isFree: serializer.fromJson<bool>(json['isFree']),
      sortOrder: serializer.fromJson<int>(json['sortOrder']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'dealId': serializer.toJson<String>(dealId),
      'productId': serializer.toJson<String?>(productId),
      'categoryId': serializer.toJson<String?>(categoryId),
      'quantity': serializer.toJson<int>(quantity),
      'isFree': serializer.toJson<bool>(isFree),
      'sortOrder': serializer.toJson<int>(sortOrder),
    };
  }

  DealItemsTableData copyWith(
          {String? id,
          String? dealId,
          Value<String?> productId = const Value.absent(),
          Value<String?> categoryId = const Value.absent(),
          int? quantity,
          bool? isFree,
          int? sortOrder}) =>
      DealItemsTableData(
        id: id ?? this.id,
        dealId: dealId ?? this.dealId,
        productId: productId.present ? productId.value : this.productId,
        categoryId: categoryId.present ? categoryId.value : this.categoryId,
        quantity: quantity ?? this.quantity,
        isFree: isFree ?? this.isFree,
        sortOrder: sortOrder ?? this.sortOrder,
      );
  DealItemsTableData copyWithCompanion(DealItemsTableCompanion data) {
    return DealItemsTableData(
      id: data.id.present ? data.id.value : this.id,
      dealId: data.dealId.present ? data.dealId.value : this.dealId,
      productId: data.productId.present ? data.productId.value : this.productId,
      categoryId:
          data.categoryId.present ? data.categoryId.value : this.categoryId,
      quantity: data.quantity.present ? data.quantity.value : this.quantity,
      isFree: data.isFree.present ? data.isFree.value : this.isFree,
      sortOrder: data.sortOrder.present ? data.sortOrder.value : this.sortOrder,
    );
  }

  @override
  String toString() {
    return (StringBuffer('DealItemsTableData(')
          ..write('id: $id, ')
          ..write('dealId: $dealId, ')
          ..write('productId: $productId, ')
          ..write('categoryId: $categoryId, ')
          ..write('quantity: $quantity, ')
          ..write('isFree: $isFree, ')
          ..write('sortOrder: $sortOrder')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, dealId, productId, categoryId, quantity, isFree, sortOrder);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is DealItemsTableData &&
          other.id == this.id &&
          other.dealId == this.dealId &&
          other.productId == this.productId &&
          other.categoryId == this.categoryId &&
          other.quantity == this.quantity &&
          other.isFree == this.isFree &&
          other.sortOrder == this.sortOrder);
}

class DealItemsTableCompanion extends UpdateCompanion<DealItemsTableData> {
  final Value<String> id;
  final Value<String> dealId;
  final Value<String?> productId;
  final Value<String?> categoryId;
  final Value<int> quantity;
  final Value<bool> isFree;
  final Value<int> sortOrder;
  final Value<int> rowid;
  const DealItemsTableCompanion({
    this.id = const Value.absent(),
    this.dealId = const Value.absent(),
    this.productId = const Value.absent(),
    this.categoryId = const Value.absent(),
    this.quantity = const Value.absent(),
    this.isFree = const Value.absent(),
    this.sortOrder = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  DealItemsTableCompanion.insert({
    required String id,
    required String dealId,
    this.productId = const Value.absent(),
    this.categoryId = const Value.absent(),
    required int quantity,
    required bool isFree,
    required int sortOrder,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        dealId = Value(dealId),
        quantity = Value(quantity),
        isFree = Value(isFree),
        sortOrder = Value(sortOrder);
  static Insertable<DealItemsTableData> custom({
    Expression<String>? id,
    Expression<String>? dealId,
    Expression<String>? productId,
    Expression<String>? categoryId,
    Expression<int>? quantity,
    Expression<bool>? isFree,
    Expression<int>? sortOrder,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (dealId != null) 'deal_id': dealId,
      if (productId != null) 'product_id': productId,
      if (categoryId != null) 'category_id': categoryId,
      if (quantity != null) 'quantity': quantity,
      if (isFree != null) 'is_free': isFree,
      if (sortOrder != null) 'sort_order': sortOrder,
      if (rowid != null) 'rowid': rowid,
    });
  }

  DealItemsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? dealId,
      Value<String?>? productId,
      Value<String?>? categoryId,
      Value<int>? quantity,
      Value<bool>? isFree,
      Value<int>? sortOrder,
      Value<int>? rowid}) {
    return DealItemsTableCompanion(
      id: id ?? this.id,
      dealId: dealId ?? this.dealId,
      productId: productId ?? this.productId,
      categoryId: categoryId ?? this.categoryId,
      quantity: quantity ?? this.quantity,
      isFree: isFree ?? this.isFree,
      sortOrder: sortOrder ?? this.sortOrder,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (dealId.present) {
      map['deal_id'] = Variable<String>(dealId.value);
    }
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (categoryId.present) {
      map['category_id'] = Variable<String>(categoryId.value);
    }
    if (quantity.present) {
      map['quantity'] = Variable<int>(quantity.value);
    }
    if (isFree.present) {
      map['is_free'] = Variable<bool>(isFree.value);
    }
    if (sortOrder.present) {
      map['sort_order'] = Variable<int>(sortOrder.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('DealItemsTableCompanion(')
          ..write('id: $id, ')
          ..write('dealId: $dealId, ')
          ..write('productId: $productId, ')
          ..write('categoryId: $categoryId, ')
          ..write('quantity: $quantity, ')
          ..write('isFree: $isFree, ')
          ..write('sortOrder: $sortOrder, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $PromotionsTableTable extends PromotionsTable
    with TableInfo<$PromotionsTableTable, PromotionsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PromotionsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _promoCodeMeta =
      const VerificationMeta('promoCode');
  @override
  late final GeneratedColumn<String> promoCode = GeneratedColumn<String>(
      'promo_code', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _typeMeta = const VerificationMeta('type');
  @override
  late final GeneratedColumn<String> type = GeneratedColumn<String>(
      'type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _discountValueMeta =
      const VerificationMeta('discountValue');
  @override
  late final GeneratedColumn<String> discountValue = GeneratedColumn<String>(
      'discount_value', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _triggerMinQtyMeta =
      const VerificationMeta('triggerMinQty');
  @override
  late final GeneratedColumn<int> triggerMinQty = GeneratedColumn<int>(
      'trigger_min_qty', aliasedName, true,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _triggerMinAmountMeta =
      const VerificationMeta('triggerMinAmount');
  @override
  late final GeneratedColumn<String> triggerMinAmount = GeneratedColumn<String>(
      'trigger_min_amount', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _triggerProductIdMeta =
      const VerificationMeta('triggerProductId');
  @override
  late final GeneratedColumn<String> triggerProductId = GeneratedColumn<String>(
      'trigger_product_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _triggerCategoryIdMeta =
      const VerificationMeta('triggerCategoryId');
  @override
  late final GeneratedColumn<String> triggerCategoryId =
      GeneratedColumn<String>('trigger_category_id', aliasedName, true,
          type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _validFromMeta =
      const VerificationMeta('validFrom');
  @override
  late final GeneratedColumn<DateTime> validFrom = GeneratedColumn<DateTime>(
      'valid_from', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _validUntilMeta =
      const VerificationMeta('validUntil');
  @override
  late final GeneratedColumn<DateTime> validUntil = GeneratedColumn<DateTime>(
      'valid_until', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _maxUsesMeta =
      const VerificationMeta('maxUses');
  @override
  late final GeneratedColumn<int> maxUses = GeneratedColumn<int>(
      'max_uses', aliasedName, true,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _usedCountMeta =
      const VerificationMeta('usedCount');
  @override
  late final GeneratedColumn<int> usedCount = GeneratedColumn<int>(
      'used_count', aliasedName, false,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(0));
  static const VerificationMeta _isActiveMeta =
      const VerificationMeta('isActive');
  @override
  late final GeneratedColumn<bool> isActive = GeneratedColumn<bool>(
      'is_active', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_active" IN (0, 1))'));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        name,
        promoCode,
        type,
        discountValue,
        triggerMinQty,
        triggerMinAmount,
        triggerProductId,
        triggerCategoryId,
        validFrom,
        validUntil,
        maxUses,
        usedCount,
        isActive
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'promotions';
  @override
  VerificationContext validateIntegrity(
      Insertable<PromotionsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('promo_code')) {
      context.handle(_promoCodeMeta,
          promoCode.isAcceptableOrUnknown(data['promo_code']!, _promoCodeMeta));
    }
    if (data.containsKey('type')) {
      context.handle(
          _typeMeta, type.isAcceptableOrUnknown(data['type']!, _typeMeta));
    } else if (isInserting) {
      context.missing(_typeMeta);
    }
    if (data.containsKey('discount_value')) {
      context.handle(
          _discountValueMeta,
          discountValue.isAcceptableOrUnknown(
              data['discount_value']!, _discountValueMeta));
    } else if (isInserting) {
      context.missing(_discountValueMeta);
    }
    if (data.containsKey('trigger_min_qty')) {
      context.handle(
          _triggerMinQtyMeta,
          triggerMinQty.isAcceptableOrUnknown(
              data['trigger_min_qty']!, _triggerMinQtyMeta));
    }
    if (data.containsKey('trigger_min_amount')) {
      context.handle(
          _triggerMinAmountMeta,
          triggerMinAmount.isAcceptableOrUnknown(
              data['trigger_min_amount']!, _triggerMinAmountMeta));
    }
    if (data.containsKey('trigger_product_id')) {
      context.handle(
          _triggerProductIdMeta,
          triggerProductId.isAcceptableOrUnknown(
              data['trigger_product_id']!, _triggerProductIdMeta));
    }
    if (data.containsKey('trigger_category_id')) {
      context.handle(
          _triggerCategoryIdMeta,
          triggerCategoryId.isAcceptableOrUnknown(
              data['trigger_category_id']!, _triggerCategoryIdMeta));
    }
    if (data.containsKey('valid_from')) {
      context.handle(_validFromMeta,
          validFrom.isAcceptableOrUnknown(data['valid_from']!, _validFromMeta));
    }
    if (data.containsKey('valid_until')) {
      context.handle(
          _validUntilMeta,
          validUntil.isAcceptableOrUnknown(
              data['valid_until']!, _validUntilMeta));
    }
    if (data.containsKey('max_uses')) {
      context.handle(_maxUsesMeta,
          maxUses.isAcceptableOrUnknown(data['max_uses']!, _maxUsesMeta));
    }
    if (data.containsKey('used_count')) {
      context.handle(_usedCountMeta,
          usedCount.isAcceptableOrUnknown(data['used_count']!, _usedCountMeta));
    }
    if (data.containsKey('is_active')) {
      context.handle(_isActiveMeta,
          isActive.isAcceptableOrUnknown(data['is_active']!, _isActiveMeta));
    } else if (isInserting) {
      context.missing(_isActiveMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  PromotionsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PromotionsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      promoCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}promo_code']),
      type: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}type'])!,
      discountValue: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}discount_value'])!,
      triggerMinQty: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}trigger_min_qty']),
      triggerMinAmount: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}trigger_min_amount']),
      triggerProductId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}trigger_product_id']),
      triggerCategoryId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}trigger_category_id']),
      validFrom: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}valid_from']),
      validUntil: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}valid_until']),
      maxUses: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}max_uses']),
      usedCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}used_count'])!,
      isActive: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_active'])!,
    );
  }

  @override
  $PromotionsTableTable createAlias(String alias) {
    return $PromotionsTableTable(attachedDatabase, alias);
  }
}

class PromotionsTableData extends DataClass
    implements Insertable<PromotionsTableData> {
  final String id;
  final String name;

  /// Cashier-entered code to activate this promotion; null for automatic promotions.
  final String? promoCode;

  /// Discount type string, e.g. "percent", "flat", "bogo".
  final String type;

  /// Discount magnitude as TEXT (Decimal); meaning depends on [type].
  final String discountValue;
  final int? triggerMinQty;
  final String? triggerMinAmount;
  final String? triggerProductId;
  final String? triggerCategoryId;
  final DateTime? validFrom;
  final DateTime? validUntil;

  /// Null means unlimited uses; enforced server-side on upload.
  final int? maxUses;

  /// Synced from server for display only — the server is authoritative for enforcement.
  final int usedCount;
  final bool isActive;
  const PromotionsTableData(
      {required this.id,
      required this.name,
      this.promoCode,
      required this.type,
      required this.discountValue,
      this.triggerMinQty,
      this.triggerMinAmount,
      this.triggerProductId,
      this.triggerCategoryId,
      this.validFrom,
      this.validUntil,
      this.maxUses,
      required this.usedCount,
      required this.isActive});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    if (!nullToAbsent || promoCode != null) {
      map['promo_code'] = Variable<String>(promoCode);
    }
    map['type'] = Variable<String>(type);
    map['discount_value'] = Variable<String>(discountValue);
    if (!nullToAbsent || triggerMinQty != null) {
      map['trigger_min_qty'] = Variable<int>(triggerMinQty);
    }
    if (!nullToAbsent || triggerMinAmount != null) {
      map['trigger_min_amount'] = Variable<String>(triggerMinAmount);
    }
    if (!nullToAbsent || triggerProductId != null) {
      map['trigger_product_id'] = Variable<String>(triggerProductId);
    }
    if (!nullToAbsent || triggerCategoryId != null) {
      map['trigger_category_id'] = Variable<String>(triggerCategoryId);
    }
    if (!nullToAbsent || validFrom != null) {
      map['valid_from'] = Variable<DateTime>(validFrom);
    }
    if (!nullToAbsent || validUntil != null) {
      map['valid_until'] = Variable<DateTime>(validUntil);
    }
    if (!nullToAbsent || maxUses != null) {
      map['max_uses'] = Variable<int>(maxUses);
    }
    map['used_count'] = Variable<int>(usedCount);
    map['is_active'] = Variable<bool>(isActive);
    return map;
  }

  PromotionsTableCompanion toCompanion(bool nullToAbsent) {
    return PromotionsTableCompanion(
      id: Value(id),
      name: Value(name),
      promoCode: promoCode == null && nullToAbsent
          ? const Value.absent()
          : Value(promoCode),
      type: Value(type),
      discountValue: Value(discountValue),
      triggerMinQty: triggerMinQty == null && nullToAbsent
          ? const Value.absent()
          : Value(triggerMinQty),
      triggerMinAmount: triggerMinAmount == null && nullToAbsent
          ? const Value.absent()
          : Value(triggerMinAmount),
      triggerProductId: triggerProductId == null && nullToAbsent
          ? const Value.absent()
          : Value(triggerProductId),
      triggerCategoryId: triggerCategoryId == null && nullToAbsent
          ? const Value.absent()
          : Value(triggerCategoryId),
      validFrom: validFrom == null && nullToAbsent
          ? const Value.absent()
          : Value(validFrom),
      validUntil: validUntil == null && nullToAbsent
          ? const Value.absent()
          : Value(validUntil),
      maxUses: maxUses == null && nullToAbsent
          ? const Value.absent()
          : Value(maxUses),
      usedCount: Value(usedCount),
      isActive: Value(isActive),
    );
  }

  factory PromotionsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PromotionsTableData(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      promoCode: serializer.fromJson<String?>(json['promoCode']),
      type: serializer.fromJson<String>(json['type']),
      discountValue: serializer.fromJson<String>(json['discountValue']),
      triggerMinQty: serializer.fromJson<int?>(json['triggerMinQty']),
      triggerMinAmount: serializer.fromJson<String?>(json['triggerMinAmount']),
      triggerProductId: serializer.fromJson<String?>(json['triggerProductId']),
      triggerCategoryId:
          serializer.fromJson<String?>(json['triggerCategoryId']),
      validFrom: serializer.fromJson<DateTime?>(json['validFrom']),
      validUntil: serializer.fromJson<DateTime?>(json['validUntil']),
      maxUses: serializer.fromJson<int?>(json['maxUses']),
      usedCount: serializer.fromJson<int>(json['usedCount']),
      isActive: serializer.fromJson<bool>(json['isActive']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'promoCode': serializer.toJson<String?>(promoCode),
      'type': serializer.toJson<String>(type),
      'discountValue': serializer.toJson<String>(discountValue),
      'triggerMinQty': serializer.toJson<int?>(triggerMinQty),
      'triggerMinAmount': serializer.toJson<String?>(triggerMinAmount),
      'triggerProductId': serializer.toJson<String?>(triggerProductId),
      'triggerCategoryId': serializer.toJson<String?>(triggerCategoryId),
      'validFrom': serializer.toJson<DateTime?>(validFrom),
      'validUntil': serializer.toJson<DateTime?>(validUntil),
      'maxUses': serializer.toJson<int?>(maxUses),
      'usedCount': serializer.toJson<int>(usedCount),
      'isActive': serializer.toJson<bool>(isActive),
    };
  }

  PromotionsTableData copyWith(
          {String? id,
          String? name,
          Value<String?> promoCode = const Value.absent(),
          String? type,
          String? discountValue,
          Value<int?> triggerMinQty = const Value.absent(),
          Value<String?> triggerMinAmount = const Value.absent(),
          Value<String?> triggerProductId = const Value.absent(),
          Value<String?> triggerCategoryId = const Value.absent(),
          Value<DateTime?> validFrom = const Value.absent(),
          Value<DateTime?> validUntil = const Value.absent(),
          Value<int?> maxUses = const Value.absent(),
          int? usedCount,
          bool? isActive}) =>
      PromotionsTableData(
        id: id ?? this.id,
        name: name ?? this.name,
        promoCode: promoCode.present ? promoCode.value : this.promoCode,
        type: type ?? this.type,
        discountValue: discountValue ?? this.discountValue,
        triggerMinQty:
            triggerMinQty.present ? triggerMinQty.value : this.triggerMinQty,
        triggerMinAmount: triggerMinAmount.present
            ? triggerMinAmount.value
            : this.triggerMinAmount,
        triggerProductId: triggerProductId.present
            ? triggerProductId.value
            : this.triggerProductId,
        triggerCategoryId: triggerCategoryId.present
            ? triggerCategoryId.value
            : this.triggerCategoryId,
        validFrom: validFrom.present ? validFrom.value : this.validFrom,
        validUntil: validUntil.present ? validUntil.value : this.validUntil,
        maxUses: maxUses.present ? maxUses.value : this.maxUses,
        usedCount: usedCount ?? this.usedCount,
        isActive: isActive ?? this.isActive,
      );
  PromotionsTableData copyWithCompanion(PromotionsTableCompanion data) {
    return PromotionsTableData(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      promoCode: data.promoCode.present ? data.promoCode.value : this.promoCode,
      type: data.type.present ? data.type.value : this.type,
      discountValue: data.discountValue.present
          ? data.discountValue.value
          : this.discountValue,
      triggerMinQty: data.triggerMinQty.present
          ? data.triggerMinQty.value
          : this.triggerMinQty,
      triggerMinAmount: data.triggerMinAmount.present
          ? data.triggerMinAmount.value
          : this.triggerMinAmount,
      triggerProductId: data.triggerProductId.present
          ? data.triggerProductId.value
          : this.triggerProductId,
      triggerCategoryId: data.triggerCategoryId.present
          ? data.triggerCategoryId.value
          : this.triggerCategoryId,
      validFrom: data.validFrom.present ? data.validFrom.value : this.validFrom,
      validUntil:
          data.validUntil.present ? data.validUntil.value : this.validUntil,
      maxUses: data.maxUses.present ? data.maxUses.value : this.maxUses,
      usedCount: data.usedCount.present ? data.usedCount.value : this.usedCount,
      isActive: data.isActive.present ? data.isActive.value : this.isActive,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PromotionsTableData(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('promoCode: $promoCode, ')
          ..write('type: $type, ')
          ..write('discountValue: $discountValue, ')
          ..write('triggerMinQty: $triggerMinQty, ')
          ..write('triggerMinAmount: $triggerMinAmount, ')
          ..write('triggerProductId: $triggerProductId, ')
          ..write('triggerCategoryId: $triggerCategoryId, ')
          ..write('validFrom: $validFrom, ')
          ..write('validUntil: $validUntil, ')
          ..write('maxUses: $maxUses, ')
          ..write('usedCount: $usedCount, ')
          ..write('isActive: $isActive')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      name,
      promoCode,
      type,
      discountValue,
      triggerMinQty,
      triggerMinAmount,
      triggerProductId,
      triggerCategoryId,
      validFrom,
      validUntil,
      maxUses,
      usedCount,
      isActive);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PromotionsTableData &&
          other.id == this.id &&
          other.name == this.name &&
          other.promoCode == this.promoCode &&
          other.type == this.type &&
          other.discountValue == this.discountValue &&
          other.triggerMinQty == this.triggerMinQty &&
          other.triggerMinAmount == this.triggerMinAmount &&
          other.triggerProductId == this.triggerProductId &&
          other.triggerCategoryId == this.triggerCategoryId &&
          other.validFrom == this.validFrom &&
          other.validUntil == this.validUntil &&
          other.maxUses == this.maxUses &&
          other.usedCount == this.usedCount &&
          other.isActive == this.isActive);
}

class PromotionsTableCompanion extends UpdateCompanion<PromotionsTableData> {
  final Value<String> id;
  final Value<String> name;
  final Value<String?> promoCode;
  final Value<String> type;
  final Value<String> discountValue;
  final Value<int?> triggerMinQty;
  final Value<String?> triggerMinAmount;
  final Value<String?> triggerProductId;
  final Value<String?> triggerCategoryId;
  final Value<DateTime?> validFrom;
  final Value<DateTime?> validUntil;
  final Value<int?> maxUses;
  final Value<int> usedCount;
  final Value<bool> isActive;
  final Value<int> rowid;
  const PromotionsTableCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.promoCode = const Value.absent(),
    this.type = const Value.absent(),
    this.discountValue = const Value.absent(),
    this.triggerMinQty = const Value.absent(),
    this.triggerMinAmount = const Value.absent(),
    this.triggerProductId = const Value.absent(),
    this.triggerCategoryId = const Value.absent(),
    this.validFrom = const Value.absent(),
    this.validUntil = const Value.absent(),
    this.maxUses = const Value.absent(),
    this.usedCount = const Value.absent(),
    this.isActive = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  PromotionsTableCompanion.insert({
    required String id,
    required String name,
    this.promoCode = const Value.absent(),
    required String type,
    required String discountValue,
    this.triggerMinQty = const Value.absent(),
    this.triggerMinAmount = const Value.absent(),
    this.triggerProductId = const Value.absent(),
    this.triggerCategoryId = const Value.absent(),
    this.validFrom = const Value.absent(),
    this.validUntil = const Value.absent(),
    this.maxUses = const Value.absent(),
    this.usedCount = const Value.absent(),
    required bool isActive,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        name = Value(name),
        type = Value(type),
        discountValue = Value(discountValue),
        isActive = Value(isActive);
  static Insertable<PromotionsTableData> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? promoCode,
    Expression<String>? type,
    Expression<String>? discountValue,
    Expression<int>? triggerMinQty,
    Expression<String>? triggerMinAmount,
    Expression<String>? triggerProductId,
    Expression<String>? triggerCategoryId,
    Expression<DateTime>? validFrom,
    Expression<DateTime>? validUntil,
    Expression<int>? maxUses,
    Expression<int>? usedCount,
    Expression<bool>? isActive,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (promoCode != null) 'promo_code': promoCode,
      if (type != null) 'type': type,
      if (discountValue != null) 'discount_value': discountValue,
      if (triggerMinQty != null) 'trigger_min_qty': triggerMinQty,
      if (triggerMinAmount != null) 'trigger_min_amount': triggerMinAmount,
      if (triggerProductId != null) 'trigger_product_id': triggerProductId,
      if (triggerCategoryId != null) 'trigger_category_id': triggerCategoryId,
      if (validFrom != null) 'valid_from': validFrom,
      if (validUntil != null) 'valid_until': validUntil,
      if (maxUses != null) 'max_uses': maxUses,
      if (usedCount != null) 'used_count': usedCount,
      if (isActive != null) 'is_active': isActive,
      if (rowid != null) 'rowid': rowid,
    });
  }

  PromotionsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? name,
      Value<String?>? promoCode,
      Value<String>? type,
      Value<String>? discountValue,
      Value<int?>? triggerMinQty,
      Value<String?>? triggerMinAmount,
      Value<String?>? triggerProductId,
      Value<String?>? triggerCategoryId,
      Value<DateTime?>? validFrom,
      Value<DateTime?>? validUntil,
      Value<int?>? maxUses,
      Value<int>? usedCount,
      Value<bool>? isActive,
      Value<int>? rowid}) {
    return PromotionsTableCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      promoCode: promoCode ?? this.promoCode,
      type: type ?? this.type,
      discountValue: discountValue ?? this.discountValue,
      triggerMinQty: triggerMinQty ?? this.triggerMinQty,
      triggerMinAmount: triggerMinAmount ?? this.triggerMinAmount,
      triggerProductId: triggerProductId ?? this.triggerProductId,
      triggerCategoryId: triggerCategoryId ?? this.triggerCategoryId,
      validFrom: validFrom ?? this.validFrom,
      validUntil: validUntil ?? this.validUntil,
      maxUses: maxUses ?? this.maxUses,
      usedCount: usedCount ?? this.usedCount,
      isActive: isActive ?? this.isActive,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (promoCode.present) {
      map['promo_code'] = Variable<String>(promoCode.value);
    }
    if (type.present) {
      map['type'] = Variable<String>(type.value);
    }
    if (discountValue.present) {
      map['discount_value'] = Variable<String>(discountValue.value);
    }
    if (triggerMinQty.present) {
      map['trigger_min_qty'] = Variable<int>(triggerMinQty.value);
    }
    if (triggerMinAmount.present) {
      map['trigger_min_amount'] = Variable<String>(triggerMinAmount.value);
    }
    if (triggerProductId.present) {
      map['trigger_product_id'] = Variable<String>(triggerProductId.value);
    }
    if (triggerCategoryId.present) {
      map['trigger_category_id'] = Variable<String>(triggerCategoryId.value);
    }
    if (validFrom.present) {
      map['valid_from'] = Variable<DateTime>(validFrom.value);
    }
    if (validUntil.present) {
      map['valid_until'] = Variable<DateTime>(validUntil.value);
    }
    if (maxUses.present) {
      map['max_uses'] = Variable<int>(maxUses.value);
    }
    if (usedCount.present) {
      map['used_count'] = Variable<int>(usedCount.value);
    }
    if (isActive.present) {
      map['is_active'] = Variable<bool>(isActive.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PromotionsTableCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('promoCode: $promoCode, ')
          ..write('type: $type, ')
          ..write('discountValue: $discountValue, ')
          ..write('triggerMinQty: $triggerMinQty, ')
          ..write('triggerMinAmount: $triggerMinAmount, ')
          ..write('triggerProductId: $triggerProductId, ')
          ..write('triggerCategoryId: $triggerCategoryId, ')
          ..write('validFrom: $validFrom, ')
          ..write('validUntil: $validUntil, ')
          ..write('maxUses: $maxUses, ')
          ..write('usedCount: $usedCount, ')
          ..write('isActive: $isActive, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalSalesTableTable extends LocalSalesTable
    with TableInfo<$LocalSalesTableTable, LocalSalesTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalSalesTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _originProofMeta =
      const VerificationMeta('originProof');
  @override
  late final GeneratedColumn<String> originProof = GeneratedColumn<String>(
      'origin_proof', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _sessionIdMeta =
      const VerificationMeta('sessionId');
  @override
  late final GeneratedColumn<String> sessionId = GeneratedColumn<String>(
      'session_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _cashierIdMeta =
      const VerificationMeta('cashierId');
  @override
  late final GeneratedColumn<String> cashierId = GeneratedColumn<String>(
      'cashier_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _saleNumberMeta =
      const VerificationMeta('saleNumber');
  @override
  late final GeneratedColumn<String> saleNumber = GeneratedColumn<String>(
      'sale_number', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: true,
      defaultConstraints: GeneratedColumn.constraintIsAlways('UNIQUE'));
  static const VerificationMeta _soldAtMeta = const VerificationMeta('soldAt');
  @override
  late final GeneratedColumn<DateTime> soldAt = GeneratedColumn<DateTime>(
      'sold_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _cashierNameMeta =
      const VerificationMeta('cashierName');
  @override
  late final GeneratedColumn<String> cashierName = GeneratedColumn<String>(
      'cashier_name', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('COMPLETED'));
  static const VerificationMeta _subtotalMeta =
      const VerificationMeta('subtotal');
  @override
  late final GeneratedColumn<String> subtotal = GeneratedColumn<String>(
      'subtotal', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _discountMeta =
      const VerificationMeta('discount');
  @override
  late final GeneratedColumn<String> discount = GeneratedColumn<String>(
      'discount', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _totalMeta = const VerificationMeta('total');
  @override
  late final GeneratedColumn<String> total = GeneratedColumn<String>(
      'total', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _taxAmountMeta =
      const VerificationMeta('taxAmount');
  @override
  late final GeneratedColumn<String> taxAmount = GeneratedColumn<String>(
      'tax_amount', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _taxRateMeta =
      const VerificationMeta('taxRate');
  @override
  late final GeneratedColumn<String> taxRate = GeneratedColumn<String>(
      'tax_rate', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _promotionIdMeta =
      const VerificationMeta('promotionId');
  @override
  late final GeneratedColumn<String> promotionId = GeneratedColumn<String>(
      'promotion_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _dealIdMeta = const VerificationMeta('dealId');
  @override
  late final GeneratedColumn<String> dealId = GeneratedColumn<String>(
      'deal_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _syncedMeta = const VerificationMeta('synced');
  @override
  late final GeneratedColumn<bool> synced = GeneratedColumn<bool>(
      'synced', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("synced" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime,
      requiredDuringInsert: false,
      defaultValue: currentDateAndTime);
  static const VerificationMeta _needsReviewMeta =
      const VerificationMeta('needsReview');
  @override
  late final GeneratedColumn<bool> needsReview = GeneratedColumn<bool>(
      'needs_review', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("needs_review" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _syncErrorMeta =
      const VerificationMeta('syncError');
  @override
  late final GeneratedColumn<String> syncError = GeneratedColumn<String>(
      'sync_error', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        originProof,
        sessionId,
        cashierId,
        saleNumber,
        soldAt,
        cashierName,
        status,
        subtotal,
        discount,
        total,
        taxAmount,
        taxRate,
        promotionId,
        dealId,
        synced,
        createdAt,
        needsReview,
        syncError
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_sales';
  @override
  VerificationContext validateIntegrity(
      Insertable<LocalSalesTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('origin_proof')) {
      context.handle(
          _originProofMeta,
          originProof.isAcceptableOrUnknown(
              data['origin_proof']!, _originProofMeta));
    }
    if (data.containsKey('session_id')) {
      context.handle(_sessionIdMeta,
          sessionId.isAcceptableOrUnknown(data['session_id']!, _sessionIdMeta));
    }
    if (data.containsKey('cashier_id')) {
      context.handle(_cashierIdMeta,
          cashierId.isAcceptableOrUnknown(data['cashier_id']!, _cashierIdMeta));
    }
    if (data.containsKey('sale_number')) {
      context.handle(
          _saleNumberMeta,
          saleNumber.isAcceptableOrUnknown(
              data['sale_number']!, _saleNumberMeta));
    } else if (isInserting) {
      context.missing(_saleNumberMeta);
    }
    if (data.containsKey('sold_at')) {
      context.handle(_soldAtMeta,
          soldAt.isAcceptableOrUnknown(data['sold_at']!, _soldAtMeta));
    } else if (isInserting) {
      context.missing(_soldAtMeta);
    }
    if (data.containsKey('cashier_name')) {
      context.handle(
          _cashierNameMeta,
          cashierName.isAcceptableOrUnknown(
              data['cashier_name']!, _cashierNameMeta));
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    }
    if (data.containsKey('subtotal')) {
      context.handle(_subtotalMeta,
          subtotal.isAcceptableOrUnknown(data['subtotal']!, _subtotalMeta));
    } else if (isInserting) {
      context.missing(_subtotalMeta);
    }
    if (data.containsKey('discount')) {
      context.handle(_discountMeta,
          discount.isAcceptableOrUnknown(data['discount']!, _discountMeta));
    } else if (isInserting) {
      context.missing(_discountMeta);
    }
    if (data.containsKey('total')) {
      context.handle(
          _totalMeta, total.isAcceptableOrUnknown(data['total']!, _totalMeta));
    } else if (isInserting) {
      context.missing(_totalMeta);
    }
    if (data.containsKey('tax_amount')) {
      context.handle(_taxAmountMeta,
          taxAmount.isAcceptableOrUnknown(data['tax_amount']!, _taxAmountMeta));
    } else if (isInserting) {
      context.missing(_taxAmountMeta);
    }
    if (data.containsKey('tax_rate')) {
      context.handle(_taxRateMeta,
          taxRate.isAcceptableOrUnknown(data['tax_rate']!, _taxRateMeta));
    }
    if (data.containsKey('promotion_id')) {
      context.handle(
          _promotionIdMeta,
          promotionId.isAcceptableOrUnknown(
              data['promotion_id']!, _promotionIdMeta));
    }
    if (data.containsKey('deal_id')) {
      context.handle(_dealIdMeta,
          dealId.isAcceptableOrUnknown(data['deal_id']!, _dealIdMeta));
    }
    if (data.containsKey('synced')) {
      context.handle(_syncedMeta,
          synced.isAcceptableOrUnknown(data['synced']!, _syncedMeta));
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    }
    if (data.containsKey('needs_review')) {
      context.handle(
          _needsReviewMeta,
          needsReview.isAcceptableOrUnknown(
              data['needs_review']!, _needsReviewMeta));
    }
    if (data.containsKey('sync_error')) {
      context.handle(_syncErrorMeta,
          syncError.isAcceptableOrUnknown(data['sync_error']!, _syncErrorMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalSalesTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalSalesTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      originProof: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}origin_proof']),
      sessionId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}session_id']),
      cashierId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}cashier_id']),
      saleNumber: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sale_number'])!,
      soldAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}sold_at'])!,
      cashierName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}cashier_name']),
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      subtotal: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}subtotal'])!,
      discount: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}discount'])!,
      total: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}total'])!,
      taxAmount: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}tax_amount'])!,
      taxRate: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}tax_rate']),
      promotionId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}promotion_id']),
      dealId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}deal_id']),
      synced: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}synced'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      needsReview: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}needs_review'])!,
      syncError: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sync_error']),
    );
  }

  @override
  $LocalSalesTableTable createAlias(String alias) {
    return $LocalSalesTableTable(attachedDatabase, alias);
  }
}

class LocalSalesTableData extends DataClass
    implements Insertable<LocalSalesTableData> {
  /// Client-generated UUID v4 — preserved as the server-side primary key on upload.
  final String id;

  /// Human-readable sale number unique per device (e.g. "S2024000001").
  /// UNIQUE constraint lets [SaleDao.saleByNumber] quickly detect duplicates.
  final String? originProof;
  final String? sessionId;
  final String? cashierId;
  final String saleNumber;
  final DateTime soldAt;

  /// The signed-in cashier's display name at the moment of submission.
  /// Captured client-side because an offline-queued sale has no server
  /// round-trip to resolve it from `user_id` until it syncs.
  final String? cashierName;

  /// Authoritative cloud status when known. Queued rows remain COMPLETED
  /// locally because they represent finalized, not draft, transactions.
  final String status;

  /// Pre-discount, pre-tax item total. Stored as TEXT (Decimal).
  final String subtotal;
  final String discount;
  final String total;
  final String taxAmount;
  final String? taxRate;
  final String? promotionId;
  final String? dealId;

  /// False until this sale has been successfully uploaded to the server.
  final bool synced;
  final DateTime createdAt;

  /// True once the server has rejected this sale for a deterministic reason
  /// (see [PosUploadResult.retryable]) — retrying would fail identically, so
  /// [SaleDao.unsynced] excludes it from future upload batches instead of
  /// resubmitting it on every sync tick forever. Surfaced to the cashier via
  /// [syncError] until an admin resolves it server-side.
  final bool needsReview;

  /// The server's rejection message, retained for [needsReview] sales so the
  /// sync status banner can keep showing it after the sale stops retrying.
  final String? syncError;
  const LocalSalesTableData(
      {required this.id,
      this.originProof,
      this.sessionId,
      this.cashierId,
      required this.saleNumber,
      required this.soldAt,
      this.cashierName,
      required this.status,
      required this.subtotal,
      required this.discount,
      required this.total,
      required this.taxAmount,
      this.taxRate,
      this.promotionId,
      this.dealId,
      required this.synced,
      required this.createdAt,
      required this.needsReview,
      this.syncError});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    if (!nullToAbsent || originProof != null) {
      map['origin_proof'] = Variable<String>(originProof);
    }
    if (!nullToAbsent || sessionId != null) {
      map['session_id'] = Variable<String>(sessionId);
    }
    if (!nullToAbsent || cashierId != null) {
      map['cashier_id'] = Variable<String>(cashierId);
    }
    map['sale_number'] = Variable<String>(saleNumber);
    map['sold_at'] = Variable<DateTime>(soldAt);
    if (!nullToAbsent || cashierName != null) {
      map['cashier_name'] = Variable<String>(cashierName);
    }
    map['status'] = Variable<String>(status);
    map['subtotal'] = Variable<String>(subtotal);
    map['discount'] = Variable<String>(discount);
    map['total'] = Variable<String>(total);
    map['tax_amount'] = Variable<String>(taxAmount);
    if (!nullToAbsent || taxRate != null) {
      map['tax_rate'] = Variable<String>(taxRate);
    }
    if (!nullToAbsent || promotionId != null) {
      map['promotion_id'] = Variable<String>(promotionId);
    }
    if (!nullToAbsent || dealId != null) {
      map['deal_id'] = Variable<String>(dealId);
    }
    map['synced'] = Variable<bool>(synced);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['needs_review'] = Variable<bool>(needsReview);
    if (!nullToAbsent || syncError != null) {
      map['sync_error'] = Variable<String>(syncError);
    }
    return map;
  }

  LocalSalesTableCompanion toCompanion(bool nullToAbsent) {
    return LocalSalesTableCompanion(
      id: Value(id),
      originProof: originProof == null && nullToAbsent
          ? const Value.absent()
          : Value(originProof),
      sessionId: sessionId == null && nullToAbsent
          ? const Value.absent()
          : Value(sessionId),
      cashierId: cashierId == null && nullToAbsent
          ? const Value.absent()
          : Value(cashierId),
      saleNumber: Value(saleNumber),
      soldAt: Value(soldAt),
      cashierName: cashierName == null && nullToAbsent
          ? const Value.absent()
          : Value(cashierName),
      status: Value(status),
      subtotal: Value(subtotal),
      discount: Value(discount),
      total: Value(total),
      taxAmount: Value(taxAmount),
      taxRate: taxRate == null && nullToAbsent
          ? const Value.absent()
          : Value(taxRate),
      promotionId: promotionId == null && nullToAbsent
          ? const Value.absent()
          : Value(promotionId),
      dealId:
          dealId == null && nullToAbsent ? const Value.absent() : Value(dealId),
      synced: Value(synced),
      createdAt: Value(createdAt),
      needsReview: Value(needsReview),
      syncError: syncError == null && nullToAbsent
          ? const Value.absent()
          : Value(syncError),
    );
  }

  factory LocalSalesTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalSalesTableData(
      id: serializer.fromJson<String>(json['id']),
      originProof: serializer.fromJson<String?>(json['originProof']),
      sessionId: serializer.fromJson<String?>(json['sessionId']),
      cashierId: serializer.fromJson<String?>(json['cashierId']),
      saleNumber: serializer.fromJson<String>(json['saleNumber']),
      soldAt: serializer.fromJson<DateTime>(json['soldAt']),
      cashierName: serializer.fromJson<String?>(json['cashierName']),
      status: serializer.fromJson<String>(json['status']),
      subtotal: serializer.fromJson<String>(json['subtotal']),
      discount: serializer.fromJson<String>(json['discount']),
      total: serializer.fromJson<String>(json['total']),
      taxAmount: serializer.fromJson<String>(json['taxAmount']),
      taxRate: serializer.fromJson<String?>(json['taxRate']),
      promotionId: serializer.fromJson<String?>(json['promotionId']),
      dealId: serializer.fromJson<String?>(json['dealId']),
      synced: serializer.fromJson<bool>(json['synced']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      needsReview: serializer.fromJson<bool>(json['needsReview']),
      syncError: serializer.fromJson<String?>(json['syncError']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'originProof': serializer.toJson<String?>(originProof),
      'sessionId': serializer.toJson<String?>(sessionId),
      'cashierId': serializer.toJson<String?>(cashierId),
      'saleNumber': serializer.toJson<String>(saleNumber),
      'soldAt': serializer.toJson<DateTime>(soldAt),
      'cashierName': serializer.toJson<String?>(cashierName),
      'status': serializer.toJson<String>(status),
      'subtotal': serializer.toJson<String>(subtotal),
      'discount': serializer.toJson<String>(discount),
      'total': serializer.toJson<String>(total),
      'taxAmount': serializer.toJson<String>(taxAmount),
      'taxRate': serializer.toJson<String?>(taxRate),
      'promotionId': serializer.toJson<String?>(promotionId),
      'dealId': serializer.toJson<String?>(dealId),
      'synced': serializer.toJson<bool>(synced),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'needsReview': serializer.toJson<bool>(needsReview),
      'syncError': serializer.toJson<String?>(syncError),
    };
  }

  LocalSalesTableData copyWith(
          {String? id,
          Value<String?> originProof = const Value.absent(),
          Value<String?> sessionId = const Value.absent(),
          Value<String?> cashierId = const Value.absent(),
          String? saleNumber,
          DateTime? soldAt,
          Value<String?> cashierName = const Value.absent(),
          String? status,
          String? subtotal,
          String? discount,
          String? total,
          String? taxAmount,
          Value<String?> taxRate = const Value.absent(),
          Value<String?> promotionId = const Value.absent(),
          Value<String?> dealId = const Value.absent(),
          bool? synced,
          DateTime? createdAt,
          bool? needsReview,
          Value<String?> syncError = const Value.absent()}) =>
      LocalSalesTableData(
        id: id ?? this.id,
        originProof: originProof.present ? originProof.value : this.originProof,
        sessionId: sessionId.present ? sessionId.value : this.sessionId,
        cashierId: cashierId.present ? cashierId.value : this.cashierId,
        saleNumber: saleNumber ?? this.saleNumber,
        soldAt: soldAt ?? this.soldAt,
        cashierName: cashierName.present ? cashierName.value : this.cashierName,
        status: status ?? this.status,
        subtotal: subtotal ?? this.subtotal,
        discount: discount ?? this.discount,
        total: total ?? this.total,
        taxAmount: taxAmount ?? this.taxAmount,
        taxRate: taxRate.present ? taxRate.value : this.taxRate,
        promotionId: promotionId.present ? promotionId.value : this.promotionId,
        dealId: dealId.present ? dealId.value : this.dealId,
        synced: synced ?? this.synced,
        createdAt: createdAt ?? this.createdAt,
        needsReview: needsReview ?? this.needsReview,
        syncError: syncError.present ? syncError.value : this.syncError,
      );
  LocalSalesTableData copyWithCompanion(LocalSalesTableCompanion data) {
    return LocalSalesTableData(
      id: data.id.present ? data.id.value : this.id,
      originProof:
          data.originProof.present ? data.originProof.value : this.originProof,
      sessionId: data.sessionId.present ? data.sessionId.value : this.sessionId,
      cashierId: data.cashierId.present ? data.cashierId.value : this.cashierId,
      saleNumber:
          data.saleNumber.present ? data.saleNumber.value : this.saleNumber,
      soldAt: data.soldAt.present ? data.soldAt.value : this.soldAt,
      cashierName:
          data.cashierName.present ? data.cashierName.value : this.cashierName,
      status: data.status.present ? data.status.value : this.status,
      subtotal: data.subtotal.present ? data.subtotal.value : this.subtotal,
      discount: data.discount.present ? data.discount.value : this.discount,
      total: data.total.present ? data.total.value : this.total,
      taxAmount: data.taxAmount.present ? data.taxAmount.value : this.taxAmount,
      taxRate: data.taxRate.present ? data.taxRate.value : this.taxRate,
      promotionId:
          data.promotionId.present ? data.promotionId.value : this.promotionId,
      dealId: data.dealId.present ? data.dealId.value : this.dealId,
      synced: data.synced.present ? data.synced.value : this.synced,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      needsReview:
          data.needsReview.present ? data.needsReview.value : this.needsReview,
      syncError: data.syncError.present ? data.syncError.value : this.syncError,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalSalesTableData(')
          ..write('id: $id, ')
          ..write('originProof: $originProof, ')
          ..write('sessionId: $sessionId, ')
          ..write('cashierId: $cashierId, ')
          ..write('saleNumber: $saleNumber, ')
          ..write('soldAt: $soldAt, ')
          ..write('cashierName: $cashierName, ')
          ..write('status: $status, ')
          ..write('subtotal: $subtotal, ')
          ..write('discount: $discount, ')
          ..write('total: $total, ')
          ..write('taxAmount: $taxAmount, ')
          ..write('taxRate: $taxRate, ')
          ..write('promotionId: $promotionId, ')
          ..write('dealId: $dealId, ')
          ..write('synced: $synced, ')
          ..write('createdAt: $createdAt, ')
          ..write('needsReview: $needsReview, ')
          ..write('syncError: $syncError')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      originProof,
      sessionId,
      cashierId,
      saleNumber,
      soldAt,
      cashierName,
      status,
      subtotal,
      discount,
      total,
      taxAmount,
      taxRate,
      promotionId,
      dealId,
      synced,
      createdAt,
      needsReview,
      syncError);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalSalesTableData &&
          other.id == this.id &&
          other.originProof == this.originProof &&
          other.sessionId == this.sessionId &&
          other.cashierId == this.cashierId &&
          other.saleNumber == this.saleNumber &&
          other.soldAt == this.soldAt &&
          other.cashierName == this.cashierName &&
          other.status == this.status &&
          other.subtotal == this.subtotal &&
          other.discount == this.discount &&
          other.total == this.total &&
          other.taxAmount == this.taxAmount &&
          other.taxRate == this.taxRate &&
          other.promotionId == this.promotionId &&
          other.dealId == this.dealId &&
          other.synced == this.synced &&
          other.createdAt == this.createdAt &&
          other.needsReview == this.needsReview &&
          other.syncError == this.syncError);
}

class LocalSalesTableCompanion extends UpdateCompanion<LocalSalesTableData> {
  final Value<String> id;
  final Value<String?> originProof;
  final Value<String?> sessionId;
  final Value<String?> cashierId;
  final Value<String> saleNumber;
  final Value<DateTime> soldAt;
  final Value<String?> cashierName;
  final Value<String> status;
  final Value<String> subtotal;
  final Value<String> discount;
  final Value<String> total;
  final Value<String> taxAmount;
  final Value<String?> taxRate;
  final Value<String?> promotionId;
  final Value<String?> dealId;
  final Value<bool> synced;
  final Value<DateTime> createdAt;
  final Value<bool> needsReview;
  final Value<String?> syncError;
  final Value<int> rowid;
  const LocalSalesTableCompanion({
    this.id = const Value.absent(),
    this.originProof = const Value.absent(),
    this.sessionId = const Value.absent(),
    this.cashierId = const Value.absent(),
    this.saleNumber = const Value.absent(),
    this.soldAt = const Value.absent(),
    this.cashierName = const Value.absent(),
    this.status = const Value.absent(),
    this.subtotal = const Value.absent(),
    this.discount = const Value.absent(),
    this.total = const Value.absent(),
    this.taxAmount = const Value.absent(),
    this.taxRate = const Value.absent(),
    this.promotionId = const Value.absent(),
    this.dealId = const Value.absent(),
    this.synced = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.needsReview = const Value.absent(),
    this.syncError = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalSalesTableCompanion.insert({
    required String id,
    this.originProof = const Value.absent(),
    this.sessionId = const Value.absent(),
    this.cashierId = const Value.absent(),
    required String saleNumber,
    required DateTime soldAt,
    this.cashierName = const Value.absent(),
    this.status = const Value.absent(),
    required String subtotal,
    required String discount,
    required String total,
    required String taxAmount,
    this.taxRate = const Value.absent(),
    this.promotionId = const Value.absent(),
    this.dealId = const Value.absent(),
    this.synced = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.needsReview = const Value.absent(),
    this.syncError = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        saleNumber = Value(saleNumber),
        soldAt = Value(soldAt),
        subtotal = Value(subtotal),
        discount = Value(discount),
        total = Value(total),
        taxAmount = Value(taxAmount);
  static Insertable<LocalSalesTableData> custom({
    Expression<String>? id,
    Expression<String>? originProof,
    Expression<String>? sessionId,
    Expression<String>? cashierId,
    Expression<String>? saleNumber,
    Expression<DateTime>? soldAt,
    Expression<String>? cashierName,
    Expression<String>? status,
    Expression<String>? subtotal,
    Expression<String>? discount,
    Expression<String>? total,
    Expression<String>? taxAmount,
    Expression<String>? taxRate,
    Expression<String>? promotionId,
    Expression<String>? dealId,
    Expression<bool>? synced,
    Expression<DateTime>? createdAt,
    Expression<bool>? needsReview,
    Expression<String>? syncError,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (originProof != null) 'origin_proof': originProof,
      if (sessionId != null) 'session_id': sessionId,
      if (cashierId != null) 'cashier_id': cashierId,
      if (saleNumber != null) 'sale_number': saleNumber,
      if (soldAt != null) 'sold_at': soldAt,
      if (cashierName != null) 'cashier_name': cashierName,
      if (status != null) 'status': status,
      if (subtotal != null) 'subtotal': subtotal,
      if (discount != null) 'discount': discount,
      if (total != null) 'total': total,
      if (taxAmount != null) 'tax_amount': taxAmount,
      if (taxRate != null) 'tax_rate': taxRate,
      if (promotionId != null) 'promotion_id': promotionId,
      if (dealId != null) 'deal_id': dealId,
      if (synced != null) 'synced': synced,
      if (createdAt != null) 'created_at': createdAt,
      if (needsReview != null) 'needs_review': needsReview,
      if (syncError != null) 'sync_error': syncError,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalSalesTableCompanion copyWith(
      {Value<String>? id,
      Value<String?>? originProof,
      Value<String?>? sessionId,
      Value<String?>? cashierId,
      Value<String>? saleNumber,
      Value<DateTime>? soldAt,
      Value<String?>? cashierName,
      Value<String>? status,
      Value<String>? subtotal,
      Value<String>? discount,
      Value<String>? total,
      Value<String>? taxAmount,
      Value<String?>? taxRate,
      Value<String?>? promotionId,
      Value<String?>? dealId,
      Value<bool>? synced,
      Value<DateTime>? createdAt,
      Value<bool>? needsReview,
      Value<String?>? syncError,
      Value<int>? rowid}) {
    return LocalSalesTableCompanion(
      id: id ?? this.id,
      originProof: originProof ?? this.originProof,
      sessionId: sessionId ?? this.sessionId,
      cashierId: cashierId ?? this.cashierId,
      saleNumber: saleNumber ?? this.saleNumber,
      soldAt: soldAt ?? this.soldAt,
      cashierName: cashierName ?? this.cashierName,
      status: status ?? this.status,
      subtotal: subtotal ?? this.subtotal,
      discount: discount ?? this.discount,
      total: total ?? this.total,
      taxAmount: taxAmount ?? this.taxAmount,
      taxRate: taxRate ?? this.taxRate,
      promotionId: promotionId ?? this.promotionId,
      dealId: dealId ?? this.dealId,
      synced: synced ?? this.synced,
      createdAt: createdAt ?? this.createdAt,
      needsReview: needsReview ?? this.needsReview,
      syncError: syncError ?? this.syncError,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (originProof.present) {
      map['origin_proof'] = Variable<String>(originProof.value);
    }
    if (sessionId.present) {
      map['session_id'] = Variable<String>(sessionId.value);
    }
    if (cashierId.present) {
      map['cashier_id'] = Variable<String>(cashierId.value);
    }
    if (saleNumber.present) {
      map['sale_number'] = Variable<String>(saleNumber.value);
    }
    if (soldAt.present) {
      map['sold_at'] = Variable<DateTime>(soldAt.value);
    }
    if (cashierName.present) {
      map['cashier_name'] = Variable<String>(cashierName.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (subtotal.present) {
      map['subtotal'] = Variable<String>(subtotal.value);
    }
    if (discount.present) {
      map['discount'] = Variable<String>(discount.value);
    }
    if (total.present) {
      map['total'] = Variable<String>(total.value);
    }
    if (taxAmount.present) {
      map['tax_amount'] = Variable<String>(taxAmount.value);
    }
    if (taxRate.present) {
      map['tax_rate'] = Variable<String>(taxRate.value);
    }
    if (promotionId.present) {
      map['promotion_id'] = Variable<String>(promotionId.value);
    }
    if (dealId.present) {
      map['deal_id'] = Variable<String>(dealId.value);
    }
    if (synced.present) {
      map['synced'] = Variable<bool>(synced.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (needsReview.present) {
      map['needs_review'] = Variable<bool>(needsReview.value);
    }
    if (syncError.present) {
      map['sync_error'] = Variable<String>(syncError.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalSalesTableCompanion(')
          ..write('id: $id, ')
          ..write('originProof: $originProof, ')
          ..write('sessionId: $sessionId, ')
          ..write('cashierId: $cashierId, ')
          ..write('saleNumber: $saleNumber, ')
          ..write('soldAt: $soldAt, ')
          ..write('cashierName: $cashierName, ')
          ..write('status: $status, ')
          ..write('subtotal: $subtotal, ')
          ..write('discount: $discount, ')
          ..write('total: $total, ')
          ..write('taxAmount: $taxAmount, ')
          ..write('taxRate: $taxRate, ')
          ..write('promotionId: $promotionId, ')
          ..write('dealId: $dealId, ')
          ..write('synced: $synced, ')
          ..write('createdAt: $createdAt, ')
          ..write('needsReview: $needsReview, ')
          ..write('syncError: $syncError, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalSaleItemsTableTable extends LocalSaleItemsTable
    with TableInfo<$LocalSaleItemsTableTable, LocalSaleItemsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalSaleItemsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _saleIdMeta = const VerificationMeta('saleId');
  @override
  late final GeneratedColumn<String> saleId = GeneratedColumn<String>(
      'sale_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _variantIdMeta =
      const VerificationMeta('variantId');
  @override
  late final GeneratedColumn<String> variantId = GeneratedColumn<String>(
      'variant_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _productIdMeta =
      const VerificationMeta('productId');
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
      'product_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _productNameMeta =
      const VerificationMeta('productName');
  @override
  late final GeneratedColumn<String> productName = GeneratedColumn<String>(
      'product_name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _quantityMeta =
      const VerificationMeta('quantity');
  @override
  late final GeneratedColumn<String> quantity = GeneratedColumn<String>(
      'quantity', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _unitPriceMeta =
      const VerificationMeta('unitPrice');
  @override
  late final GeneratedColumn<String> unitPrice = GeneratedColumn<String>(
      'unit_price', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _discountMeta =
      const VerificationMeta('discount');
  @override
  late final GeneratedColumn<String> discount = GeneratedColumn<String>(
      'discount', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _totalMeta = const VerificationMeta('total');
  @override
  late final GeneratedColumn<String> total = GeneratedColumn<String>(
      'total', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _parentItemIdMeta =
      const VerificationMeta('parentItemId');
  @override
  late final GeneratedColumn<String> parentItemId = GeneratedColumn<String>(
      'parent_item_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _satisfiesOptionGroupIdMeta =
      const VerificationMeta('satisfiesOptionGroupId');
  @override
  late final GeneratedColumn<String> satisfiesOptionGroupId =
      GeneratedColumn<String>('satisfies_option_group_id', aliasedName, true,
          type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _componentOptionIdMeta =
      const VerificationMeta('componentOptionId');
  @override
  late final GeneratedColumn<String> componentOptionId =
      GeneratedColumn<String>('component_option_id', aliasedName, true,
          type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        saleId,
        variantId,
        productId,
        productName,
        quantity,
        unitPrice,
        discount,
        total,
        parentItemId,
        satisfiesOptionGroupId,
        componentOptionId
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_sale_items';
  @override
  VerificationContext validateIntegrity(
      Insertable<LocalSaleItemsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('sale_id')) {
      context.handle(_saleIdMeta,
          saleId.isAcceptableOrUnknown(data['sale_id']!, _saleIdMeta));
    } else if (isInserting) {
      context.missing(_saleIdMeta);
    }
    if (data.containsKey('variant_id')) {
      context.handle(_variantIdMeta,
          variantId.isAcceptableOrUnknown(data['variant_id']!, _variantIdMeta));
    }
    if (data.containsKey('product_id')) {
      context.handle(_productIdMeta,
          productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta));
    } else if (isInserting) {
      context.missing(_productIdMeta);
    }
    if (data.containsKey('product_name')) {
      context.handle(
          _productNameMeta,
          productName.isAcceptableOrUnknown(
              data['product_name']!, _productNameMeta));
    } else if (isInserting) {
      context.missing(_productNameMeta);
    }
    if (data.containsKey('quantity')) {
      context.handle(_quantityMeta,
          quantity.isAcceptableOrUnknown(data['quantity']!, _quantityMeta));
    } else if (isInserting) {
      context.missing(_quantityMeta);
    }
    if (data.containsKey('unit_price')) {
      context.handle(_unitPriceMeta,
          unitPrice.isAcceptableOrUnknown(data['unit_price']!, _unitPriceMeta));
    } else if (isInserting) {
      context.missing(_unitPriceMeta);
    }
    if (data.containsKey('discount')) {
      context.handle(_discountMeta,
          discount.isAcceptableOrUnknown(data['discount']!, _discountMeta));
    } else if (isInserting) {
      context.missing(_discountMeta);
    }
    if (data.containsKey('total')) {
      context.handle(
          _totalMeta, total.isAcceptableOrUnknown(data['total']!, _totalMeta));
    } else if (isInserting) {
      context.missing(_totalMeta);
    }
    if (data.containsKey('parent_item_id')) {
      context.handle(
          _parentItemIdMeta,
          parentItemId.isAcceptableOrUnknown(
              data['parent_item_id']!, _parentItemIdMeta));
    }
    if (data.containsKey('satisfies_option_group_id')) {
      context.handle(
          _satisfiesOptionGroupIdMeta,
          satisfiesOptionGroupId.isAcceptableOrUnknown(
              data['satisfies_option_group_id']!, _satisfiesOptionGroupIdMeta));
    }
    if (data.containsKey('component_option_id')) {
      context.handle(
          _componentOptionIdMeta,
          componentOptionId.isAcceptableOrUnknown(
              data['component_option_id']!, _componentOptionIdMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalSaleItemsTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalSaleItemsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      saleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sale_id'])!,
      variantId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}variant_id']),
      productId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_id'])!,
      productName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_name'])!,
      quantity: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}quantity'])!,
      unitPrice: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}unit_price'])!,
      discount: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}discount'])!,
      total: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}total'])!,
      parentItemId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}parent_item_id']),
      satisfiesOptionGroupId: attachedDatabase.typeMapping.read(
          DriftSqlType.string,
          data['${effectivePrefix}satisfies_option_group_id']),
      componentOptionId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}component_option_id']),
    );
  }

  @override
  $LocalSaleItemsTableTable createAlias(String alias) {
    return $LocalSaleItemsTableTable(attachedDatabase, alias);
  }
}

class LocalSaleItemsTableData extends DataClass
    implements Insertable<LocalSaleItemsTableData> {
  final String id;
  final String saleId;
  final String? variantId;
  final String productId;

  /// Name captured at sale time — not a foreign key so it survives catalog renames.
  final String productName;
  final String quantity;
  final String unitPrice;
  final String discount;
  final String total;

  /// Laptop Store shareable-inventory model — set together only on a
  /// selected 'inventory_component' line (e.g. a RAM stick), which is
  /// otherwise an ordinary row in this same table, not a nested child —
  /// see cart_service.dart's CartItem. Null for every normal item.
  final String? parentItemId;
  final String? satisfiesOptionGroupId;
  final String? componentOptionId;
  const LocalSaleItemsTableData(
      {required this.id,
      required this.saleId,
      this.variantId,
      required this.productId,
      required this.productName,
      required this.quantity,
      required this.unitPrice,
      required this.discount,
      required this.total,
      this.parentItemId,
      this.satisfiesOptionGroupId,
      this.componentOptionId});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['sale_id'] = Variable<String>(saleId);
    if (!nullToAbsent || variantId != null) {
      map['variant_id'] = Variable<String>(variantId);
    }
    map['product_id'] = Variable<String>(productId);
    map['product_name'] = Variable<String>(productName);
    map['quantity'] = Variable<String>(quantity);
    map['unit_price'] = Variable<String>(unitPrice);
    map['discount'] = Variable<String>(discount);
    map['total'] = Variable<String>(total);
    if (!nullToAbsent || parentItemId != null) {
      map['parent_item_id'] = Variable<String>(parentItemId);
    }
    if (!nullToAbsent || satisfiesOptionGroupId != null) {
      map['satisfies_option_group_id'] =
          Variable<String>(satisfiesOptionGroupId);
    }
    if (!nullToAbsent || componentOptionId != null) {
      map['component_option_id'] = Variable<String>(componentOptionId);
    }
    return map;
  }

  LocalSaleItemsTableCompanion toCompanion(bool nullToAbsent) {
    return LocalSaleItemsTableCompanion(
      id: Value(id),
      saleId: Value(saleId),
      variantId: variantId == null && nullToAbsent
          ? const Value.absent()
          : Value(variantId),
      productId: Value(productId),
      productName: Value(productName),
      quantity: Value(quantity),
      unitPrice: Value(unitPrice),
      discount: Value(discount),
      total: Value(total),
      parentItemId: parentItemId == null && nullToAbsent
          ? const Value.absent()
          : Value(parentItemId),
      satisfiesOptionGroupId: satisfiesOptionGroupId == null && nullToAbsent
          ? const Value.absent()
          : Value(satisfiesOptionGroupId),
      componentOptionId: componentOptionId == null && nullToAbsent
          ? const Value.absent()
          : Value(componentOptionId),
    );
  }

  factory LocalSaleItemsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalSaleItemsTableData(
      id: serializer.fromJson<String>(json['id']),
      saleId: serializer.fromJson<String>(json['saleId']),
      variantId: serializer.fromJson<String?>(json['variantId']),
      productId: serializer.fromJson<String>(json['productId']),
      productName: serializer.fromJson<String>(json['productName']),
      quantity: serializer.fromJson<String>(json['quantity']),
      unitPrice: serializer.fromJson<String>(json['unitPrice']),
      discount: serializer.fromJson<String>(json['discount']),
      total: serializer.fromJson<String>(json['total']),
      parentItemId: serializer.fromJson<String?>(json['parentItemId']),
      satisfiesOptionGroupId:
          serializer.fromJson<String?>(json['satisfiesOptionGroupId']),
      componentOptionId:
          serializer.fromJson<String?>(json['componentOptionId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'saleId': serializer.toJson<String>(saleId),
      'variantId': serializer.toJson<String?>(variantId),
      'productId': serializer.toJson<String>(productId),
      'productName': serializer.toJson<String>(productName),
      'quantity': serializer.toJson<String>(quantity),
      'unitPrice': serializer.toJson<String>(unitPrice),
      'discount': serializer.toJson<String>(discount),
      'total': serializer.toJson<String>(total),
      'parentItemId': serializer.toJson<String?>(parentItemId),
      'satisfiesOptionGroupId':
          serializer.toJson<String?>(satisfiesOptionGroupId),
      'componentOptionId': serializer.toJson<String?>(componentOptionId),
    };
  }

  LocalSaleItemsTableData copyWith(
          {String? id,
          String? saleId,
          Value<String?> variantId = const Value.absent(),
          String? productId,
          String? productName,
          String? quantity,
          String? unitPrice,
          String? discount,
          String? total,
          Value<String?> parentItemId = const Value.absent(),
          Value<String?> satisfiesOptionGroupId = const Value.absent(),
          Value<String?> componentOptionId = const Value.absent()}) =>
      LocalSaleItemsTableData(
        id: id ?? this.id,
        saleId: saleId ?? this.saleId,
        variantId: variantId.present ? variantId.value : this.variantId,
        productId: productId ?? this.productId,
        productName: productName ?? this.productName,
        quantity: quantity ?? this.quantity,
        unitPrice: unitPrice ?? this.unitPrice,
        discount: discount ?? this.discount,
        total: total ?? this.total,
        parentItemId:
            parentItemId.present ? parentItemId.value : this.parentItemId,
        satisfiesOptionGroupId: satisfiesOptionGroupId.present
            ? satisfiesOptionGroupId.value
            : this.satisfiesOptionGroupId,
        componentOptionId: componentOptionId.present
            ? componentOptionId.value
            : this.componentOptionId,
      );
  LocalSaleItemsTableData copyWithCompanion(LocalSaleItemsTableCompanion data) {
    return LocalSaleItemsTableData(
      id: data.id.present ? data.id.value : this.id,
      saleId: data.saleId.present ? data.saleId.value : this.saleId,
      variantId: data.variantId.present ? data.variantId.value : this.variantId,
      productId: data.productId.present ? data.productId.value : this.productId,
      productName:
          data.productName.present ? data.productName.value : this.productName,
      quantity: data.quantity.present ? data.quantity.value : this.quantity,
      unitPrice: data.unitPrice.present ? data.unitPrice.value : this.unitPrice,
      discount: data.discount.present ? data.discount.value : this.discount,
      total: data.total.present ? data.total.value : this.total,
      parentItemId: data.parentItemId.present
          ? data.parentItemId.value
          : this.parentItemId,
      satisfiesOptionGroupId: data.satisfiesOptionGroupId.present
          ? data.satisfiesOptionGroupId.value
          : this.satisfiesOptionGroupId,
      componentOptionId: data.componentOptionId.present
          ? data.componentOptionId.value
          : this.componentOptionId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalSaleItemsTableData(')
          ..write('id: $id, ')
          ..write('saleId: $saleId, ')
          ..write('variantId: $variantId, ')
          ..write('productId: $productId, ')
          ..write('productName: $productName, ')
          ..write('quantity: $quantity, ')
          ..write('unitPrice: $unitPrice, ')
          ..write('discount: $discount, ')
          ..write('total: $total, ')
          ..write('parentItemId: $parentItemId, ')
          ..write('satisfiesOptionGroupId: $satisfiesOptionGroupId, ')
          ..write('componentOptionId: $componentOptionId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      saleId,
      variantId,
      productId,
      productName,
      quantity,
      unitPrice,
      discount,
      total,
      parentItemId,
      satisfiesOptionGroupId,
      componentOptionId);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalSaleItemsTableData &&
          other.id == this.id &&
          other.saleId == this.saleId &&
          other.variantId == this.variantId &&
          other.productId == this.productId &&
          other.productName == this.productName &&
          other.quantity == this.quantity &&
          other.unitPrice == this.unitPrice &&
          other.discount == this.discount &&
          other.total == this.total &&
          other.parentItemId == this.parentItemId &&
          other.satisfiesOptionGroupId == this.satisfiesOptionGroupId &&
          other.componentOptionId == this.componentOptionId);
}

class LocalSaleItemsTableCompanion
    extends UpdateCompanion<LocalSaleItemsTableData> {
  final Value<String> id;
  final Value<String> saleId;
  final Value<String?> variantId;
  final Value<String> productId;
  final Value<String> productName;
  final Value<String> quantity;
  final Value<String> unitPrice;
  final Value<String> discount;
  final Value<String> total;
  final Value<String?> parentItemId;
  final Value<String?> satisfiesOptionGroupId;
  final Value<String?> componentOptionId;
  final Value<int> rowid;
  const LocalSaleItemsTableCompanion({
    this.id = const Value.absent(),
    this.saleId = const Value.absent(),
    this.variantId = const Value.absent(),
    this.productId = const Value.absent(),
    this.productName = const Value.absent(),
    this.quantity = const Value.absent(),
    this.unitPrice = const Value.absent(),
    this.discount = const Value.absent(),
    this.total = const Value.absent(),
    this.parentItemId = const Value.absent(),
    this.satisfiesOptionGroupId = const Value.absent(),
    this.componentOptionId = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalSaleItemsTableCompanion.insert({
    required String id,
    required String saleId,
    this.variantId = const Value.absent(),
    required String productId,
    required String productName,
    required String quantity,
    required String unitPrice,
    required String discount,
    required String total,
    this.parentItemId = const Value.absent(),
    this.satisfiesOptionGroupId = const Value.absent(),
    this.componentOptionId = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        saleId = Value(saleId),
        productId = Value(productId),
        productName = Value(productName),
        quantity = Value(quantity),
        unitPrice = Value(unitPrice),
        discount = Value(discount),
        total = Value(total);
  static Insertable<LocalSaleItemsTableData> custom({
    Expression<String>? id,
    Expression<String>? saleId,
    Expression<String>? variantId,
    Expression<String>? productId,
    Expression<String>? productName,
    Expression<String>? quantity,
    Expression<String>? unitPrice,
    Expression<String>? discount,
    Expression<String>? total,
    Expression<String>? parentItemId,
    Expression<String>? satisfiesOptionGroupId,
    Expression<String>? componentOptionId,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (saleId != null) 'sale_id': saleId,
      if (variantId != null) 'variant_id': variantId,
      if (productId != null) 'product_id': productId,
      if (productName != null) 'product_name': productName,
      if (quantity != null) 'quantity': quantity,
      if (unitPrice != null) 'unit_price': unitPrice,
      if (discount != null) 'discount': discount,
      if (total != null) 'total': total,
      if (parentItemId != null) 'parent_item_id': parentItemId,
      if (satisfiesOptionGroupId != null)
        'satisfies_option_group_id': satisfiesOptionGroupId,
      if (componentOptionId != null) 'component_option_id': componentOptionId,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalSaleItemsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? saleId,
      Value<String?>? variantId,
      Value<String>? productId,
      Value<String>? productName,
      Value<String>? quantity,
      Value<String>? unitPrice,
      Value<String>? discount,
      Value<String>? total,
      Value<String?>? parentItemId,
      Value<String?>? satisfiesOptionGroupId,
      Value<String?>? componentOptionId,
      Value<int>? rowid}) {
    return LocalSaleItemsTableCompanion(
      id: id ?? this.id,
      saleId: saleId ?? this.saleId,
      variantId: variantId ?? this.variantId,
      productId: productId ?? this.productId,
      productName: productName ?? this.productName,
      quantity: quantity ?? this.quantity,
      unitPrice: unitPrice ?? this.unitPrice,
      discount: discount ?? this.discount,
      total: total ?? this.total,
      parentItemId: parentItemId ?? this.parentItemId,
      satisfiesOptionGroupId:
          satisfiesOptionGroupId ?? this.satisfiesOptionGroupId,
      componentOptionId: componentOptionId ?? this.componentOptionId,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (saleId.present) {
      map['sale_id'] = Variable<String>(saleId.value);
    }
    if (variantId.present) {
      map['variant_id'] = Variable<String>(variantId.value);
    }
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (productName.present) {
      map['product_name'] = Variable<String>(productName.value);
    }
    if (quantity.present) {
      map['quantity'] = Variable<String>(quantity.value);
    }
    if (unitPrice.present) {
      map['unit_price'] = Variable<String>(unitPrice.value);
    }
    if (discount.present) {
      map['discount'] = Variable<String>(discount.value);
    }
    if (total.present) {
      map['total'] = Variable<String>(total.value);
    }
    if (parentItemId.present) {
      map['parent_item_id'] = Variable<String>(parentItemId.value);
    }
    if (satisfiesOptionGroupId.present) {
      map['satisfies_option_group_id'] =
          Variable<String>(satisfiesOptionGroupId.value);
    }
    if (componentOptionId.present) {
      map['component_option_id'] = Variable<String>(componentOptionId.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalSaleItemsTableCompanion(')
          ..write('id: $id, ')
          ..write('saleId: $saleId, ')
          ..write('variantId: $variantId, ')
          ..write('productId: $productId, ')
          ..write('productName: $productName, ')
          ..write('quantity: $quantity, ')
          ..write('unitPrice: $unitPrice, ')
          ..write('discount: $discount, ')
          ..write('total: $total, ')
          ..write('parentItemId: $parentItemId, ')
          ..write('satisfiesOptionGroupId: $satisfiesOptionGroupId, ')
          ..write('componentOptionId: $componentOptionId, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalSaleItemOptionsTableTable extends LocalSaleItemOptionsTable
    with
        TableInfo<$LocalSaleItemOptionsTableTable,
            LocalSaleItemOptionsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalSaleItemOptionsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _saleItemIdMeta =
      const VerificationMeta('saleItemId');
  @override
  late final GeneratedColumn<String> saleItemId = GeneratedColumn<String>(
      'sale_item_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _variantOptionIdMeta =
      const VerificationMeta('variantOptionId');
  @override
  late final GeneratedColumn<String> variantOptionId = GeneratedColumn<String>(
      'product_option_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _optionNameMeta =
      const VerificationMeta('optionName');
  @override
  late final GeneratedColumn<String> optionName = GeneratedColumn<String>(
      'option_name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _priceAdjustmentMeta =
      const VerificationMeta('priceAdjustment');
  @override
  late final GeneratedColumn<String> priceAdjustment = GeneratedColumn<String>(
      'price_adjustment', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns =>
      [id, saleItemId, variantOptionId, optionName, priceAdjustment];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_sale_item_options';
  @override
  VerificationContext validateIntegrity(
      Insertable<LocalSaleItemOptionsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('sale_item_id')) {
      context.handle(
          _saleItemIdMeta,
          saleItemId.isAcceptableOrUnknown(
              data['sale_item_id']!, _saleItemIdMeta));
    } else if (isInserting) {
      context.missing(_saleItemIdMeta);
    }
    if (data.containsKey('product_option_id')) {
      context.handle(
          _variantOptionIdMeta,
          variantOptionId.isAcceptableOrUnknown(
              data['product_option_id']!, _variantOptionIdMeta));
    } else if (isInserting) {
      context.missing(_variantOptionIdMeta);
    }
    if (data.containsKey('option_name')) {
      context.handle(
          _optionNameMeta,
          optionName.isAcceptableOrUnknown(
              data['option_name']!, _optionNameMeta));
    } else if (isInserting) {
      context.missing(_optionNameMeta);
    }
    if (data.containsKey('price_adjustment')) {
      context.handle(
          _priceAdjustmentMeta,
          priceAdjustment.isAcceptableOrUnknown(
              data['price_adjustment']!, _priceAdjustmentMeta));
    } else if (isInserting) {
      context.missing(_priceAdjustmentMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalSaleItemOptionsTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalSaleItemOptionsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      saleItemId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sale_item_id'])!,
      variantOptionId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}product_option_id'])!,
      optionName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}option_name'])!,
      priceAdjustment: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}price_adjustment'])!,
    );
  }

  @override
  $LocalSaleItemOptionsTableTable createAlias(String alias) {
    return $LocalSaleItemOptionsTableTable(attachedDatabase, alias);
  }
}

class LocalSaleItemOptionsTableData extends DataClass
    implements Insertable<LocalSaleItemOptionsTableData> {
  final String id;
  final String saleItemId;
  final String variantOptionId;

  /// Snapshot of option name at sale time.
  final String optionName;

  /// Retired — Variant Options no longer carry a price (spec A1/D4). Kept
  /// physically for migration continuity; always written as "0.00".
  final String priceAdjustment;
  const LocalSaleItemOptionsTableData(
      {required this.id,
      required this.saleItemId,
      required this.variantOptionId,
      required this.optionName,
      required this.priceAdjustment});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['sale_item_id'] = Variable<String>(saleItemId);
    map['product_option_id'] = Variable<String>(variantOptionId);
    map['option_name'] = Variable<String>(optionName);
    map['price_adjustment'] = Variable<String>(priceAdjustment);
    return map;
  }

  LocalSaleItemOptionsTableCompanion toCompanion(bool nullToAbsent) {
    return LocalSaleItemOptionsTableCompanion(
      id: Value(id),
      saleItemId: Value(saleItemId),
      variantOptionId: Value(variantOptionId),
      optionName: Value(optionName),
      priceAdjustment: Value(priceAdjustment),
    );
  }

  factory LocalSaleItemOptionsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalSaleItemOptionsTableData(
      id: serializer.fromJson<String>(json['id']),
      saleItemId: serializer.fromJson<String>(json['saleItemId']),
      variantOptionId: serializer.fromJson<String>(json['variantOptionId']),
      optionName: serializer.fromJson<String>(json['optionName']),
      priceAdjustment: serializer.fromJson<String>(json['priceAdjustment']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'saleItemId': serializer.toJson<String>(saleItemId),
      'variantOptionId': serializer.toJson<String>(variantOptionId),
      'optionName': serializer.toJson<String>(optionName),
      'priceAdjustment': serializer.toJson<String>(priceAdjustment),
    };
  }

  LocalSaleItemOptionsTableData copyWith(
          {String? id,
          String? saleItemId,
          String? variantOptionId,
          String? optionName,
          String? priceAdjustment}) =>
      LocalSaleItemOptionsTableData(
        id: id ?? this.id,
        saleItemId: saleItemId ?? this.saleItemId,
        variantOptionId: variantOptionId ?? this.variantOptionId,
        optionName: optionName ?? this.optionName,
        priceAdjustment: priceAdjustment ?? this.priceAdjustment,
      );
  LocalSaleItemOptionsTableData copyWithCompanion(
      LocalSaleItemOptionsTableCompanion data) {
    return LocalSaleItemOptionsTableData(
      id: data.id.present ? data.id.value : this.id,
      saleItemId:
          data.saleItemId.present ? data.saleItemId.value : this.saleItemId,
      variantOptionId: data.variantOptionId.present
          ? data.variantOptionId.value
          : this.variantOptionId,
      optionName:
          data.optionName.present ? data.optionName.value : this.optionName,
      priceAdjustment: data.priceAdjustment.present
          ? data.priceAdjustment.value
          : this.priceAdjustment,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalSaleItemOptionsTableData(')
          ..write('id: $id, ')
          ..write('saleItemId: $saleItemId, ')
          ..write('variantOptionId: $variantOptionId, ')
          ..write('optionName: $optionName, ')
          ..write('priceAdjustment: $priceAdjustment')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, saleItemId, variantOptionId, optionName, priceAdjustment);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalSaleItemOptionsTableData &&
          other.id == this.id &&
          other.saleItemId == this.saleItemId &&
          other.variantOptionId == this.variantOptionId &&
          other.optionName == this.optionName &&
          other.priceAdjustment == this.priceAdjustment);
}

class LocalSaleItemOptionsTableCompanion
    extends UpdateCompanion<LocalSaleItemOptionsTableData> {
  final Value<String> id;
  final Value<String> saleItemId;
  final Value<String> variantOptionId;
  final Value<String> optionName;
  final Value<String> priceAdjustment;
  final Value<int> rowid;
  const LocalSaleItemOptionsTableCompanion({
    this.id = const Value.absent(),
    this.saleItemId = const Value.absent(),
    this.variantOptionId = const Value.absent(),
    this.optionName = const Value.absent(),
    this.priceAdjustment = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalSaleItemOptionsTableCompanion.insert({
    required String id,
    required String saleItemId,
    required String variantOptionId,
    required String optionName,
    required String priceAdjustment,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        saleItemId = Value(saleItemId),
        variantOptionId = Value(variantOptionId),
        optionName = Value(optionName),
        priceAdjustment = Value(priceAdjustment);
  static Insertable<LocalSaleItemOptionsTableData> custom({
    Expression<String>? id,
    Expression<String>? saleItemId,
    Expression<String>? variantOptionId,
    Expression<String>? optionName,
    Expression<String>? priceAdjustment,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (saleItemId != null) 'sale_item_id': saleItemId,
      if (variantOptionId != null) 'product_option_id': variantOptionId,
      if (optionName != null) 'option_name': optionName,
      if (priceAdjustment != null) 'price_adjustment': priceAdjustment,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalSaleItemOptionsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? saleItemId,
      Value<String>? variantOptionId,
      Value<String>? optionName,
      Value<String>? priceAdjustment,
      Value<int>? rowid}) {
    return LocalSaleItemOptionsTableCompanion(
      id: id ?? this.id,
      saleItemId: saleItemId ?? this.saleItemId,
      variantOptionId: variantOptionId ?? this.variantOptionId,
      optionName: optionName ?? this.optionName,
      priceAdjustment: priceAdjustment ?? this.priceAdjustment,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (saleItemId.present) {
      map['sale_item_id'] = Variable<String>(saleItemId.value);
    }
    if (variantOptionId.present) {
      map['product_option_id'] = Variable<String>(variantOptionId.value);
    }
    if (optionName.present) {
      map['option_name'] = Variable<String>(optionName.value);
    }
    if (priceAdjustment.present) {
      map['price_adjustment'] = Variable<String>(priceAdjustment.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalSaleItemOptionsTableCompanion(')
          ..write('id: $id, ')
          ..write('saleItemId: $saleItemId, ')
          ..write('variantOptionId: $variantOptionId, ')
          ..write('optionName: $optionName, ')
          ..write('priceAdjustment: $priceAdjustment, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalSaleItemAddonsTableTable extends LocalSaleItemAddonsTable
    with
        TableInfo<$LocalSaleItemAddonsTableTable,
            LocalSaleItemAddonsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalSaleItemAddonsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _saleItemIdMeta =
      const VerificationMeta('saleItemId');
  @override
  late final GeneratedColumn<String> saleItemId = GeneratedColumn<String>(
      'sale_item_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _addonItemIdMeta =
      const VerificationMeta('addonItemId');
  @override
  late final GeneratedColumn<String> addonItemId = GeneratedColumn<String>(
      'addon_item_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _addonNameMeta =
      const VerificationMeta('addonName');
  @override
  late final GeneratedColumn<String> addonName = GeneratedColumn<String>(
      'addon_name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _priceDeltaMeta =
      const VerificationMeta('priceDelta');
  @override
  late final GeneratedColumn<String> priceDelta = GeneratedColumn<String>(
      'price_delta', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _wasRemovedMeta =
      const VerificationMeta('wasRemoved');
  @override
  late final GeneratedColumn<bool> wasRemoved = GeneratedColumn<bool>(
      'was_removed', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("was_removed" IN (0, 1))'),
      defaultValue: const Constant(false));
  @override
  List<GeneratedColumn> get $columns =>
      [id, saleItemId, addonItemId, addonName, priceDelta, wasRemoved];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_sale_item_addons';
  @override
  VerificationContext validateIntegrity(
      Insertable<LocalSaleItemAddonsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('sale_item_id')) {
      context.handle(
          _saleItemIdMeta,
          saleItemId.isAcceptableOrUnknown(
              data['sale_item_id']!, _saleItemIdMeta));
    } else if (isInserting) {
      context.missing(_saleItemIdMeta);
    }
    if (data.containsKey('addon_item_id')) {
      context.handle(
          _addonItemIdMeta,
          addonItemId.isAcceptableOrUnknown(
              data['addon_item_id']!, _addonItemIdMeta));
    } else if (isInserting) {
      context.missing(_addonItemIdMeta);
    }
    if (data.containsKey('addon_name')) {
      context.handle(_addonNameMeta,
          addonName.isAcceptableOrUnknown(data['addon_name']!, _addonNameMeta));
    } else if (isInserting) {
      context.missing(_addonNameMeta);
    }
    if (data.containsKey('price_delta')) {
      context.handle(
          _priceDeltaMeta,
          priceDelta.isAcceptableOrUnknown(
              data['price_delta']!, _priceDeltaMeta));
    } else if (isInserting) {
      context.missing(_priceDeltaMeta);
    }
    if (data.containsKey('was_removed')) {
      context.handle(
          _wasRemovedMeta,
          wasRemoved.isAcceptableOrUnknown(
              data['was_removed']!, _wasRemovedMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalSaleItemAddonsTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalSaleItemAddonsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      saleItemId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sale_item_id'])!,
      addonItemId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}addon_item_id'])!,
      addonName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}addon_name'])!,
      priceDelta: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}price_delta'])!,
      wasRemoved: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}was_removed'])!,
    );
  }

  @override
  $LocalSaleItemAddonsTableTable createAlias(String alias) {
    return $LocalSaleItemAddonsTableTable(attachedDatabase, alias);
  }
}

class LocalSaleItemAddonsTableData extends DataClass
    implements Insertable<LocalSaleItemAddonsTableData> {
  final String id;
  final String saleItemId;
  final String addonItemId;

  /// Snapshot of the add-on name at sale time.
  final String addonName;

  /// Price delta as TEXT (Decimal), client-submitted; server re-verifies.
  final String priceDelta;
  final bool wasRemoved;
  const LocalSaleItemAddonsTableData(
      {required this.id,
      required this.saleItemId,
      required this.addonItemId,
      required this.addonName,
      required this.priceDelta,
      required this.wasRemoved});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['sale_item_id'] = Variable<String>(saleItemId);
    map['addon_item_id'] = Variable<String>(addonItemId);
    map['addon_name'] = Variable<String>(addonName);
    map['price_delta'] = Variable<String>(priceDelta);
    map['was_removed'] = Variable<bool>(wasRemoved);
    return map;
  }

  LocalSaleItemAddonsTableCompanion toCompanion(bool nullToAbsent) {
    return LocalSaleItemAddonsTableCompanion(
      id: Value(id),
      saleItemId: Value(saleItemId),
      addonItemId: Value(addonItemId),
      addonName: Value(addonName),
      priceDelta: Value(priceDelta),
      wasRemoved: Value(wasRemoved),
    );
  }

  factory LocalSaleItemAddonsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalSaleItemAddonsTableData(
      id: serializer.fromJson<String>(json['id']),
      saleItemId: serializer.fromJson<String>(json['saleItemId']),
      addonItemId: serializer.fromJson<String>(json['addonItemId']),
      addonName: serializer.fromJson<String>(json['addonName']),
      priceDelta: serializer.fromJson<String>(json['priceDelta']),
      wasRemoved: serializer.fromJson<bool>(json['wasRemoved']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'saleItemId': serializer.toJson<String>(saleItemId),
      'addonItemId': serializer.toJson<String>(addonItemId),
      'addonName': serializer.toJson<String>(addonName),
      'priceDelta': serializer.toJson<String>(priceDelta),
      'wasRemoved': serializer.toJson<bool>(wasRemoved),
    };
  }

  LocalSaleItemAddonsTableData copyWith(
          {String? id,
          String? saleItemId,
          String? addonItemId,
          String? addonName,
          String? priceDelta,
          bool? wasRemoved}) =>
      LocalSaleItemAddonsTableData(
        id: id ?? this.id,
        saleItemId: saleItemId ?? this.saleItemId,
        addonItemId: addonItemId ?? this.addonItemId,
        addonName: addonName ?? this.addonName,
        priceDelta: priceDelta ?? this.priceDelta,
        wasRemoved: wasRemoved ?? this.wasRemoved,
      );
  LocalSaleItemAddonsTableData copyWithCompanion(
      LocalSaleItemAddonsTableCompanion data) {
    return LocalSaleItemAddonsTableData(
      id: data.id.present ? data.id.value : this.id,
      saleItemId:
          data.saleItemId.present ? data.saleItemId.value : this.saleItemId,
      addonItemId:
          data.addonItemId.present ? data.addonItemId.value : this.addonItemId,
      addonName: data.addonName.present ? data.addonName.value : this.addonName,
      priceDelta:
          data.priceDelta.present ? data.priceDelta.value : this.priceDelta,
      wasRemoved:
          data.wasRemoved.present ? data.wasRemoved.value : this.wasRemoved,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalSaleItemAddonsTableData(')
          ..write('id: $id, ')
          ..write('saleItemId: $saleItemId, ')
          ..write('addonItemId: $addonItemId, ')
          ..write('addonName: $addonName, ')
          ..write('priceDelta: $priceDelta, ')
          ..write('wasRemoved: $wasRemoved')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, saleItemId, addonItemId, addonName, priceDelta, wasRemoved);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalSaleItemAddonsTableData &&
          other.id == this.id &&
          other.saleItemId == this.saleItemId &&
          other.addonItemId == this.addonItemId &&
          other.addonName == this.addonName &&
          other.priceDelta == this.priceDelta &&
          other.wasRemoved == this.wasRemoved);
}

class LocalSaleItemAddonsTableCompanion
    extends UpdateCompanion<LocalSaleItemAddonsTableData> {
  final Value<String> id;
  final Value<String> saleItemId;
  final Value<String> addonItemId;
  final Value<String> addonName;
  final Value<String> priceDelta;
  final Value<bool> wasRemoved;
  final Value<int> rowid;
  const LocalSaleItemAddonsTableCompanion({
    this.id = const Value.absent(),
    this.saleItemId = const Value.absent(),
    this.addonItemId = const Value.absent(),
    this.addonName = const Value.absent(),
    this.priceDelta = const Value.absent(),
    this.wasRemoved = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalSaleItemAddonsTableCompanion.insert({
    required String id,
    required String saleItemId,
    required String addonItemId,
    required String addonName,
    required String priceDelta,
    this.wasRemoved = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        saleItemId = Value(saleItemId),
        addonItemId = Value(addonItemId),
        addonName = Value(addonName),
        priceDelta = Value(priceDelta);
  static Insertable<LocalSaleItemAddonsTableData> custom({
    Expression<String>? id,
    Expression<String>? saleItemId,
    Expression<String>? addonItemId,
    Expression<String>? addonName,
    Expression<String>? priceDelta,
    Expression<bool>? wasRemoved,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (saleItemId != null) 'sale_item_id': saleItemId,
      if (addonItemId != null) 'addon_item_id': addonItemId,
      if (addonName != null) 'addon_name': addonName,
      if (priceDelta != null) 'price_delta': priceDelta,
      if (wasRemoved != null) 'was_removed': wasRemoved,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalSaleItemAddonsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? saleItemId,
      Value<String>? addonItemId,
      Value<String>? addonName,
      Value<String>? priceDelta,
      Value<bool>? wasRemoved,
      Value<int>? rowid}) {
    return LocalSaleItemAddonsTableCompanion(
      id: id ?? this.id,
      saleItemId: saleItemId ?? this.saleItemId,
      addonItemId: addonItemId ?? this.addonItemId,
      addonName: addonName ?? this.addonName,
      priceDelta: priceDelta ?? this.priceDelta,
      wasRemoved: wasRemoved ?? this.wasRemoved,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (saleItemId.present) {
      map['sale_item_id'] = Variable<String>(saleItemId.value);
    }
    if (addonItemId.present) {
      map['addon_item_id'] = Variable<String>(addonItemId.value);
    }
    if (addonName.present) {
      map['addon_name'] = Variable<String>(addonName.value);
    }
    if (priceDelta.present) {
      map['price_delta'] = Variable<String>(priceDelta.value);
    }
    if (wasRemoved.present) {
      map['was_removed'] = Variable<bool>(wasRemoved.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalSaleItemAddonsTableCompanion(')
          ..write('id: $id, ')
          ..write('saleItemId: $saleItemId, ')
          ..write('addonItemId: $addonItemId, ')
          ..write('addonName: $addonName, ')
          ..write('priceDelta: $priceDelta, ')
          ..write('wasRemoved: $wasRemoved, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalPaymentsTableTable extends LocalPaymentsTable
    with TableInfo<$LocalPaymentsTableTable, LocalPaymentsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalPaymentsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _saleIdMeta = const VerificationMeta('saleId');
  @override
  late final GeneratedColumn<String> saleId = GeneratedColumn<String>(
      'sale_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _paymentMethodMeta =
      const VerificationMeta('paymentMethod');
  @override
  late final GeneratedColumn<String> paymentMethod = GeneratedColumn<String>(
      'payment_method', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _amountMeta = const VerificationMeta('amount');
  @override
  late final GeneratedColumn<String> amount = GeneratedColumn<String>(
      'amount', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _referenceMeta =
      const VerificationMeta('reference');
  @override
  late final GeneratedColumn<String> reference = GeneratedColumn<String>(
      'reference', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [id, saleId, paymentMethod, amount, reference];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_payments';
  @override
  VerificationContext validateIntegrity(
      Insertable<LocalPaymentsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('sale_id')) {
      context.handle(_saleIdMeta,
          saleId.isAcceptableOrUnknown(data['sale_id']!, _saleIdMeta));
    } else if (isInserting) {
      context.missing(_saleIdMeta);
    }
    if (data.containsKey('payment_method')) {
      context.handle(
          _paymentMethodMeta,
          paymentMethod.isAcceptableOrUnknown(
              data['payment_method']!, _paymentMethodMeta));
    } else if (isInserting) {
      context.missing(_paymentMethodMeta);
    }
    if (data.containsKey('amount')) {
      context.handle(_amountMeta,
          amount.isAcceptableOrUnknown(data['amount']!, _amountMeta));
    } else if (isInserting) {
      context.missing(_amountMeta);
    }
    if (data.containsKey('reference')) {
      context.handle(_referenceMeta,
          reference.isAcceptableOrUnknown(data['reference']!, _referenceMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalPaymentsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalPaymentsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      saleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}sale_id'])!,
      paymentMethod: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payment_method'])!,
      amount: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}amount'])!,
      reference: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}reference']),
    );
  }

  @override
  $LocalPaymentsTableTable createAlias(String alias) {
    return $LocalPaymentsTableTable(attachedDatabase, alias);
  }
}

class LocalPaymentsTableData extends DataClass
    implements Insertable<LocalPaymentsTableData> {
  final String id;
  final String saleId;
  final String paymentMethod;

  /// Amount tendered for this payment method. Stored as TEXT (Decimal).
  final String amount;

  /// Optional transaction or card authorization reference.
  final String? reference;
  const LocalPaymentsTableData(
      {required this.id,
      required this.saleId,
      required this.paymentMethod,
      required this.amount,
      this.reference});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['sale_id'] = Variable<String>(saleId);
    map['payment_method'] = Variable<String>(paymentMethod);
    map['amount'] = Variable<String>(amount);
    if (!nullToAbsent || reference != null) {
      map['reference'] = Variable<String>(reference);
    }
    return map;
  }

  LocalPaymentsTableCompanion toCompanion(bool nullToAbsent) {
    return LocalPaymentsTableCompanion(
      id: Value(id),
      saleId: Value(saleId),
      paymentMethod: Value(paymentMethod),
      amount: Value(amount),
      reference: reference == null && nullToAbsent
          ? const Value.absent()
          : Value(reference),
    );
  }

  factory LocalPaymentsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalPaymentsTableData(
      id: serializer.fromJson<String>(json['id']),
      saleId: serializer.fromJson<String>(json['saleId']),
      paymentMethod: serializer.fromJson<String>(json['paymentMethod']),
      amount: serializer.fromJson<String>(json['amount']),
      reference: serializer.fromJson<String?>(json['reference']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'saleId': serializer.toJson<String>(saleId),
      'paymentMethod': serializer.toJson<String>(paymentMethod),
      'amount': serializer.toJson<String>(amount),
      'reference': serializer.toJson<String?>(reference),
    };
  }

  LocalPaymentsTableData copyWith(
          {String? id,
          String? saleId,
          String? paymentMethod,
          String? amount,
          Value<String?> reference = const Value.absent()}) =>
      LocalPaymentsTableData(
        id: id ?? this.id,
        saleId: saleId ?? this.saleId,
        paymentMethod: paymentMethod ?? this.paymentMethod,
        amount: amount ?? this.amount,
        reference: reference.present ? reference.value : this.reference,
      );
  LocalPaymentsTableData copyWithCompanion(LocalPaymentsTableCompanion data) {
    return LocalPaymentsTableData(
      id: data.id.present ? data.id.value : this.id,
      saleId: data.saleId.present ? data.saleId.value : this.saleId,
      paymentMethod: data.paymentMethod.present
          ? data.paymentMethod.value
          : this.paymentMethod,
      amount: data.amount.present ? data.amount.value : this.amount,
      reference: data.reference.present ? data.reference.value : this.reference,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalPaymentsTableData(')
          ..write('id: $id, ')
          ..write('saleId: $saleId, ')
          ..write('paymentMethod: $paymentMethod, ')
          ..write('amount: $amount, ')
          ..write('reference: $reference')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, saleId, paymentMethod, amount, reference);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalPaymentsTableData &&
          other.id == this.id &&
          other.saleId == this.saleId &&
          other.paymentMethod == this.paymentMethod &&
          other.amount == this.amount &&
          other.reference == this.reference);
}

class LocalPaymentsTableCompanion
    extends UpdateCompanion<LocalPaymentsTableData> {
  final Value<String> id;
  final Value<String> saleId;
  final Value<String> paymentMethod;
  final Value<String> amount;
  final Value<String?> reference;
  final Value<int> rowid;
  const LocalPaymentsTableCompanion({
    this.id = const Value.absent(),
    this.saleId = const Value.absent(),
    this.paymentMethod = const Value.absent(),
    this.amount = const Value.absent(),
    this.reference = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalPaymentsTableCompanion.insert({
    required String id,
    required String saleId,
    required String paymentMethod,
    required String amount,
    this.reference = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        saleId = Value(saleId),
        paymentMethod = Value(paymentMethod),
        amount = Value(amount);
  static Insertable<LocalPaymentsTableData> custom({
    Expression<String>? id,
    Expression<String>? saleId,
    Expression<String>? paymentMethod,
    Expression<String>? amount,
    Expression<String>? reference,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (saleId != null) 'sale_id': saleId,
      if (paymentMethod != null) 'payment_method': paymentMethod,
      if (amount != null) 'amount': amount,
      if (reference != null) 'reference': reference,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalPaymentsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? saleId,
      Value<String>? paymentMethod,
      Value<String>? amount,
      Value<String?>? reference,
      Value<int>? rowid}) {
    return LocalPaymentsTableCompanion(
      id: id ?? this.id,
      saleId: saleId ?? this.saleId,
      paymentMethod: paymentMethod ?? this.paymentMethod,
      amount: amount ?? this.amount,
      reference: reference ?? this.reference,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (saleId.present) {
      map['sale_id'] = Variable<String>(saleId.value);
    }
    if (paymentMethod.present) {
      map['payment_method'] = Variable<String>(paymentMethod.value);
    }
    if (amount.present) {
      map['amount'] = Variable<String>(amount.value);
    }
    if (reference.present) {
      map['reference'] = Variable<String>(reference.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalPaymentsTableCompanion(')
          ..write('id: $id, ')
          ..write('saleId: $saleId, ')
          ..write('paymentMethod: $paymentMethod, ')
          ..write('amount: $amount, ')
          ..write('reference: $reference, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalProductStockTableTable extends LocalProductStockTable
    with TableInfo<$LocalProductStockTableTable, LocalProductStockTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalProductStockTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _productIdMeta =
      const VerificationMeta('productId');
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
      'product_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _quantityMeta =
      const VerificationMeta('quantity');
  @override
  late final GeneratedColumn<String> quantity = GeneratedColumn<String>(
      'quantity', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [productId, quantity];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_product_stock';
  @override
  VerificationContext validateIntegrity(
      Insertable<LocalProductStockTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('product_id')) {
      context.handle(_productIdMeta,
          productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta));
    } else if (isInserting) {
      context.missing(_productIdMeta);
    }
    if (data.containsKey('quantity')) {
      context.handle(_quantityMeta,
          quantity.isAcceptableOrUnknown(data['quantity']!, _quantityMeta));
    } else if (isInserting) {
      context.missing(_quantityMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {productId};
  @override
  LocalProductStockTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalProductStockTableData(
      productId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_id'])!,
      quantity: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}quantity'])!,
    );
  }

  @override
  $LocalProductStockTableTable createAlias(String alias) {
    return $LocalProductStockTableTable(attachedDatabase, alias);
  }
}

class LocalProductStockTableData extends DataClass
    implements Insertable<LocalProductStockTableData> {
  final String productId;

  /// Stored as TEXT to avoid floating-point precision loss, matching
  /// ProductsTable.basePrice's convention.
  final String quantity;
  const LocalProductStockTableData(
      {required this.productId, required this.quantity});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['product_id'] = Variable<String>(productId);
    map['quantity'] = Variable<String>(quantity);
    return map;
  }

  LocalProductStockTableCompanion toCompanion(bool nullToAbsent) {
    return LocalProductStockTableCompanion(
      productId: Value(productId),
      quantity: Value(quantity),
    );
  }

  factory LocalProductStockTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalProductStockTableData(
      productId: serializer.fromJson<String>(json['productId']),
      quantity: serializer.fromJson<String>(json['quantity']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'productId': serializer.toJson<String>(productId),
      'quantity': serializer.toJson<String>(quantity),
    };
  }

  LocalProductStockTableData copyWith({String? productId, String? quantity}) =>
      LocalProductStockTableData(
        productId: productId ?? this.productId,
        quantity: quantity ?? this.quantity,
      );
  LocalProductStockTableData copyWithCompanion(
      LocalProductStockTableCompanion data) {
    return LocalProductStockTableData(
      productId: data.productId.present ? data.productId.value : this.productId,
      quantity: data.quantity.present ? data.quantity.value : this.quantity,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalProductStockTableData(')
          ..write('productId: $productId, ')
          ..write('quantity: $quantity')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(productId, quantity);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalProductStockTableData &&
          other.productId == this.productId &&
          other.quantity == this.quantity);
}

class LocalProductStockTableCompanion
    extends UpdateCompanion<LocalProductStockTableData> {
  final Value<String> productId;
  final Value<String> quantity;
  final Value<int> rowid;
  const LocalProductStockTableCompanion({
    this.productId = const Value.absent(),
    this.quantity = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalProductStockTableCompanion.insert({
    required String productId,
    required String quantity,
    this.rowid = const Value.absent(),
  })  : productId = Value(productId),
        quantity = Value(quantity);
  static Insertable<LocalProductStockTableData> custom({
    Expression<String>? productId,
    Expression<String>? quantity,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (productId != null) 'product_id': productId,
      if (quantity != null) 'quantity': quantity,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalProductStockTableCompanion copyWith(
      {Value<String>? productId, Value<String>? quantity, Value<int>? rowid}) {
    return LocalProductStockTableCompanion(
      productId: productId ?? this.productId,
      quantity: quantity ?? this.quantity,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (quantity.present) {
      map['quantity'] = Variable<String>(quantity.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalProductStockTableCompanion(')
          ..write('productId: $productId, ')
          ..write('quantity: $quantity, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $AppSettingsTableTable extends AppSettingsTable
    with TableInfo<$AppSettingsTableTable, AppSettingsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AppSettingsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
      'key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
      'value', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'app_settings';
  @override
  VerificationContext validateIntegrity(
      Insertable<AppSettingsTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
          _keyMeta, key.isAcceptableOrUnknown(data['key']!, _keyMeta));
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
          _valueMeta, value.isAcceptableOrUnknown(data['value']!, _valueMeta));
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  AppSettingsTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AppSettingsTableData(
      key: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}key'])!,
      value: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}value'])!,
    );
  }

  @override
  $AppSettingsTableTable createAlias(String alias) {
    return $AppSettingsTableTable(attachedDatabase, alias);
  }
}

class AppSettingsTableData extends DataClass
    implements Insertable<AppSettingsTableData> {
  final String key;
  final String value;
  const AppSettingsTableData({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  AppSettingsTableCompanion toCompanion(bool nullToAbsent) {
    return AppSettingsTableCompanion(
      key: Value(key),
      value: Value(value),
    );
  }

  factory AppSettingsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AppSettingsTableData(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  AppSettingsTableData copyWith({String? key, String? value}) =>
      AppSettingsTableData(
        key: key ?? this.key,
        value: value ?? this.value,
      );
  AppSettingsTableData copyWithCompanion(AppSettingsTableCompanion data) {
    return AppSettingsTableData(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AppSettingsTableData(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AppSettingsTableData &&
          other.key == this.key &&
          other.value == this.value);
}

class AppSettingsTableCompanion extends UpdateCompanion<AppSettingsTableData> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const AppSettingsTableCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AppSettingsTableCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  })  : key = Value(key),
        value = Value(value);
  static Insertable<AppSettingsTableData> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AppSettingsTableCompanion copyWith(
      {Value<String>? key, Value<String>? value, Value<int>? rowid}) {
    return AppSettingsTableCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AppSettingsTableCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $CategoriesTableTable categoriesTable =
      $CategoriesTableTable(this);
  late final $ProductsTableTable productsTable = $ProductsTableTable(this);
  late final $VariantOptionGroupsTableTable variantOptionGroupsTable =
      $VariantOptionGroupsTableTable(this);
  late final $VariantOptionsTableTable variantOptionsTable =
      $VariantOptionsTableTable(this);
  late final $VariantsTableTable variantsTable = $VariantsTableTable(this);
  late final $VariantBranchStockTableTable variantBranchStockTable =
      $VariantBranchStockTableTable(this);
  late final $AddonGroupsTableTable addonGroupsTable =
      $AddonGroupsTableTable(this);
  late final $AddonItemsTableTable addonItemsTable =
      $AddonItemsTableTable(this);
  late final $TaxRatesTableTable taxRatesTable = $TaxRatesTableTable(this);
  late final $DealsTableTable dealsTable = $DealsTableTable(this);
  late final $DealItemsTableTable dealItemsTable = $DealItemsTableTable(this);
  late final $PromotionsTableTable promotionsTable =
      $PromotionsTableTable(this);
  late final $LocalSalesTableTable localSalesTable =
      $LocalSalesTableTable(this);
  late final $LocalSaleItemsTableTable localSaleItemsTable =
      $LocalSaleItemsTableTable(this);
  late final $LocalSaleItemOptionsTableTable localSaleItemOptionsTable =
      $LocalSaleItemOptionsTableTable(this);
  late final $LocalSaleItemAddonsTableTable localSaleItemAddonsTable =
      $LocalSaleItemAddonsTableTable(this);
  late final $LocalPaymentsTableTable localPaymentsTable =
      $LocalPaymentsTableTable(this);
  late final $LocalProductStockTableTable localProductStockTable =
      $LocalProductStockTableTable(this);
  late final $AppSettingsTableTable appSettingsTable =
      $AppSettingsTableTable(this);
  late final MenuDao menuDao = MenuDao(this as AppDatabase);
  late final TaxDao taxDao = TaxDao(this as AppDatabase);
  late final SaleDao saleDao = SaleDao(this as AppDatabase);
  late final SyncDao syncDao = SyncDao(this as AppDatabase);
  late final SettingsDao settingsDao = SettingsDao(this as AppDatabase);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
        categoriesTable,
        productsTable,
        variantOptionGroupsTable,
        variantOptionsTable,
        variantsTable,
        variantBranchStockTable,
        addonGroupsTable,
        addonItemsTable,
        taxRatesTable,
        dealsTable,
        dealItemsTable,
        promotionsTable,
        localSalesTable,
        localSaleItemsTable,
        localSaleItemOptionsTable,
        localSaleItemAddonsTable,
        localPaymentsTable,
        localProductStockTable,
        appSettingsTable
      ];
}

typedef $$CategoriesTableTableCreateCompanionBuilder = CategoriesTableCompanion
    Function({
  required String id,
  required String name,
  Value<String?> description,
  Value<String?> imagePath,
  required int displayOrder,
  required bool isActive,
  Value<int> rowid,
});
typedef $$CategoriesTableTableUpdateCompanionBuilder = CategoriesTableCompanion
    Function({
  Value<String> id,
  Value<String> name,
  Value<String?> description,
  Value<String?> imagePath,
  Value<int> displayOrder,
  Value<bool> isActive,
  Value<int> rowid,
});

class $$CategoriesTableTableFilterComposer
    extends Composer<_$AppDatabase, $CategoriesTableTable> {
  $$CategoriesTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get imagePath => $composableBuilder(
      column: $table.imagePath, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnFilters(column));
}

class $$CategoriesTableTableOrderingComposer
    extends Composer<_$AppDatabase, $CategoriesTableTable> {
  $$CategoriesTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get imagePath => $composableBuilder(
      column: $table.imagePath, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnOrderings(column));
}

class $$CategoriesTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $CategoriesTableTable> {
  $$CategoriesTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<String> get imagePath =>
      $composableBuilder(column: $table.imagePath, builder: (column) => column);

  GeneratedColumn<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => column);

  GeneratedColumn<bool> get isActive =>
      $composableBuilder(column: $table.isActive, builder: (column) => column);
}

class $$CategoriesTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $CategoriesTableTable,
    CategoriesTableData,
    $$CategoriesTableTableFilterComposer,
    $$CategoriesTableTableOrderingComposer,
    $$CategoriesTableTableAnnotationComposer,
    $$CategoriesTableTableCreateCompanionBuilder,
    $$CategoriesTableTableUpdateCompanionBuilder,
    (
      CategoriesTableData,
      BaseReferences<_$AppDatabase, $CategoriesTableTable, CategoriesTableData>
    ),
    CategoriesTableData,
    PrefetchHooks Function()> {
  $$CategoriesTableTableTableManager(
      _$AppDatabase db, $CategoriesTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CategoriesTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CategoriesTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CategoriesTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String?> description = const Value.absent(),
            Value<String?> imagePath = const Value.absent(),
            Value<int> displayOrder = const Value.absent(),
            Value<bool> isActive = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CategoriesTableCompanion(
            id: id,
            name: name,
            description: description,
            imagePath: imagePath,
            displayOrder: displayOrder,
            isActive: isActive,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String name,
            Value<String?> description = const Value.absent(),
            Value<String?> imagePath = const Value.absent(),
            required int displayOrder,
            required bool isActive,
            Value<int> rowid = const Value.absent(),
          }) =>
              CategoriesTableCompanion.insert(
            id: id,
            name: name,
            description: description,
            imagePath: imagePath,
            displayOrder: displayOrder,
            isActive: isActive,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CategoriesTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $CategoriesTableTable,
    CategoriesTableData,
    $$CategoriesTableTableFilterComposer,
    $$CategoriesTableTableOrderingComposer,
    $$CategoriesTableTableAnnotationComposer,
    $$CategoriesTableTableCreateCompanionBuilder,
    $$CategoriesTableTableUpdateCompanionBuilder,
    (
      CategoriesTableData,
      BaseReferences<_$AppDatabase, $CategoriesTableTable, CategoriesTableData>
    ),
    CategoriesTableData,
    PrefetchHooks Function()>;
typedef $$ProductsTableTableCreateCompanionBuilder = ProductsTableCompanion
    Function({
  required String id,
  required String categoryId,
  required String productCode,
  required String name,
  Value<String?> description,
  required String basePrice,
  Value<String?> imagePath,
  required int displayOrder,
  required bool isActive,
  Value<bool> trackInventory,
  Value<bool> allowNegativeStock,
  Value<int> rowid,
});
typedef $$ProductsTableTableUpdateCompanionBuilder = ProductsTableCompanion
    Function({
  Value<String> id,
  Value<String> categoryId,
  Value<String> productCode,
  Value<String> name,
  Value<String?> description,
  Value<String> basePrice,
  Value<String?> imagePath,
  Value<int> displayOrder,
  Value<bool> isActive,
  Value<bool> trackInventory,
  Value<bool> allowNegativeStock,
  Value<int> rowid,
});

class $$ProductsTableTableFilterComposer
    extends Composer<_$AppDatabase, $ProductsTableTable> {
  $$ProductsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get categoryId => $composableBuilder(
      column: $table.categoryId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productCode => $composableBuilder(
      column: $table.productCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get basePrice => $composableBuilder(
      column: $table.basePrice, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get imagePath => $composableBuilder(
      column: $table.imagePath, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get trackInventory => $composableBuilder(
      column: $table.trackInventory,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get allowNegativeStock => $composableBuilder(
      column: $table.allowNegativeStock,
      builder: (column) => ColumnFilters(column));
}

class $$ProductsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $ProductsTableTable> {
  $$ProductsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get categoryId => $composableBuilder(
      column: $table.categoryId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productCode => $composableBuilder(
      column: $table.productCode, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get basePrice => $composableBuilder(
      column: $table.basePrice, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get imagePath => $composableBuilder(
      column: $table.imagePath, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get trackInventory => $composableBuilder(
      column: $table.trackInventory,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get allowNegativeStock => $composableBuilder(
      column: $table.allowNegativeStock,
      builder: (column) => ColumnOrderings(column));
}

class $$ProductsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $ProductsTableTable> {
  $$ProductsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get categoryId => $composableBuilder(
      column: $table.categoryId, builder: (column) => column);

  GeneratedColumn<String> get productCode => $composableBuilder(
      column: $table.productCode, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<String> get basePrice =>
      $composableBuilder(column: $table.basePrice, builder: (column) => column);

  GeneratedColumn<String> get imagePath =>
      $composableBuilder(column: $table.imagePath, builder: (column) => column);

  GeneratedColumn<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => column);

  GeneratedColumn<bool> get isActive =>
      $composableBuilder(column: $table.isActive, builder: (column) => column);

  GeneratedColumn<bool> get trackInventory => $composableBuilder(
      column: $table.trackInventory, builder: (column) => column);

  GeneratedColumn<bool> get allowNegativeStock => $composableBuilder(
      column: $table.allowNegativeStock, builder: (column) => column);
}

class $$ProductsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $ProductsTableTable,
    ProductsTableData,
    $$ProductsTableTableFilterComposer,
    $$ProductsTableTableOrderingComposer,
    $$ProductsTableTableAnnotationComposer,
    $$ProductsTableTableCreateCompanionBuilder,
    $$ProductsTableTableUpdateCompanionBuilder,
    (
      ProductsTableData,
      BaseReferences<_$AppDatabase, $ProductsTableTable, ProductsTableData>
    ),
    ProductsTableData,
    PrefetchHooks Function()> {
  $$ProductsTableTableTableManager(_$AppDatabase db, $ProductsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ProductsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ProductsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ProductsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> categoryId = const Value.absent(),
            Value<String> productCode = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String?> description = const Value.absent(),
            Value<String> basePrice = const Value.absent(),
            Value<String?> imagePath = const Value.absent(),
            Value<int> displayOrder = const Value.absent(),
            Value<bool> isActive = const Value.absent(),
            Value<bool> trackInventory = const Value.absent(),
            Value<bool> allowNegativeStock = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              ProductsTableCompanion(
            id: id,
            categoryId: categoryId,
            productCode: productCode,
            name: name,
            description: description,
            basePrice: basePrice,
            imagePath: imagePath,
            displayOrder: displayOrder,
            isActive: isActive,
            trackInventory: trackInventory,
            allowNegativeStock: allowNegativeStock,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String categoryId,
            required String productCode,
            required String name,
            Value<String?> description = const Value.absent(),
            required String basePrice,
            Value<String?> imagePath = const Value.absent(),
            required int displayOrder,
            required bool isActive,
            Value<bool> trackInventory = const Value.absent(),
            Value<bool> allowNegativeStock = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              ProductsTableCompanion.insert(
            id: id,
            categoryId: categoryId,
            productCode: productCode,
            name: name,
            description: description,
            basePrice: basePrice,
            imagePath: imagePath,
            displayOrder: displayOrder,
            isActive: isActive,
            trackInventory: trackInventory,
            allowNegativeStock: allowNegativeStock,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$ProductsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $ProductsTableTable,
    ProductsTableData,
    $$ProductsTableTableFilterComposer,
    $$ProductsTableTableOrderingComposer,
    $$ProductsTableTableAnnotationComposer,
    $$ProductsTableTableCreateCompanionBuilder,
    $$ProductsTableTableUpdateCompanionBuilder,
    (
      ProductsTableData,
      BaseReferences<_$AppDatabase, $ProductsTableTable, ProductsTableData>
    ),
    ProductsTableData,
    PrefetchHooks Function()>;
typedef $$VariantOptionGroupsTableTableCreateCompanionBuilder
    = VariantOptionGroupsTableCompanion Function({
  required String id,
  required String productId,
  required String name,
  required bool isRequired,
  required int displayOrder,
  Value<String> usageType,
  Value<String> allowedOptionIds,
  Value<int> rowid,
});
typedef $$VariantOptionGroupsTableTableUpdateCompanionBuilder
    = VariantOptionGroupsTableCompanion Function({
  Value<String> id,
  Value<String> productId,
  Value<String> name,
  Value<bool> isRequired,
  Value<int> displayOrder,
  Value<String> usageType,
  Value<String> allowedOptionIds,
  Value<int> rowid,
});

class $$VariantOptionGroupsTableTableFilterComposer
    extends Composer<_$AppDatabase, $VariantOptionGroupsTableTable> {
  $$VariantOptionGroupsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isRequired => $composableBuilder(
      column: $table.isRequired, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get usageType => $composableBuilder(
      column: $table.usageType, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get allowedOptionIds => $composableBuilder(
      column: $table.allowedOptionIds,
      builder: (column) => ColumnFilters(column));
}

class $$VariantOptionGroupsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $VariantOptionGroupsTableTable> {
  $$VariantOptionGroupsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isRequired => $composableBuilder(
      column: $table.isRequired, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get usageType => $composableBuilder(
      column: $table.usageType, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get allowedOptionIds => $composableBuilder(
      column: $table.allowedOptionIds,
      builder: (column) => ColumnOrderings(column));
}

class $$VariantOptionGroupsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $VariantOptionGroupsTableTable> {
  $$VariantOptionGroupsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<bool> get isRequired => $composableBuilder(
      column: $table.isRequired, builder: (column) => column);

  GeneratedColumn<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => column);

  GeneratedColumn<String> get usageType =>
      $composableBuilder(column: $table.usageType, builder: (column) => column);

  GeneratedColumn<String> get allowedOptionIds => $composableBuilder(
      column: $table.allowedOptionIds, builder: (column) => column);
}

class $$VariantOptionGroupsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $VariantOptionGroupsTableTable,
    VariantOptionGroupsTableData,
    $$VariantOptionGroupsTableTableFilterComposer,
    $$VariantOptionGroupsTableTableOrderingComposer,
    $$VariantOptionGroupsTableTableAnnotationComposer,
    $$VariantOptionGroupsTableTableCreateCompanionBuilder,
    $$VariantOptionGroupsTableTableUpdateCompanionBuilder,
    (
      VariantOptionGroupsTableData,
      BaseReferences<_$AppDatabase, $VariantOptionGroupsTableTable,
          VariantOptionGroupsTableData>
    ),
    VariantOptionGroupsTableData,
    PrefetchHooks Function()> {
  $$VariantOptionGroupsTableTableTableManager(
      _$AppDatabase db, $VariantOptionGroupsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$VariantOptionGroupsTableTableFilterComposer(
                  $db: db, $table: table),
          createOrderingComposer: () =>
              $$VariantOptionGroupsTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$VariantOptionGroupsTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> productId = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<bool> isRequired = const Value.absent(),
            Value<int> displayOrder = const Value.absent(),
            Value<String> usageType = const Value.absent(),
            Value<String> allowedOptionIds = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantOptionGroupsTableCompanion(
            id: id,
            productId: productId,
            name: name,
            isRequired: isRequired,
            displayOrder: displayOrder,
            usageType: usageType,
            allowedOptionIds: allowedOptionIds,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String productId,
            required String name,
            required bool isRequired,
            required int displayOrder,
            Value<String> usageType = const Value.absent(),
            Value<String> allowedOptionIds = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantOptionGroupsTableCompanion.insert(
            id: id,
            productId: productId,
            name: name,
            isRequired: isRequired,
            displayOrder: displayOrder,
            usageType: usageType,
            allowedOptionIds: allowedOptionIds,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$VariantOptionGroupsTableTableProcessedTableManager
    = ProcessedTableManager<
        _$AppDatabase,
        $VariantOptionGroupsTableTable,
        VariantOptionGroupsTableData,
        $$VariantOptionGroupsTableTableFilterComposer,
        $$VariantOptionGroupsTableTableOrderingComposer,
        $$VariantOptionGroupsTableTableAnnotationComposer,
        $$VariantOptionGroupsTableTableCreateCompanionBuilder,
        $$VariantOptionGroupsTableTableUpdateCompanionBuilder,
        (
          VariantOptionGroupsTableData,
          BaseReferences<_$AppDatabase, $VariantOptionGroupsTableTable,
              VariantOptionGroupsTableData>
        ),
        VariantOptionGroupsTableData,
        PrefetchHooks Function()>;
typedef $$VariantOptionsTableTableCreateCompanionBuilder
    = VariantOptionsTableCompanion Function({
  required String id,
  required String optionGroupId,
  required String name,
  required int displayOrder,
  required bool isActive,
  Value<String?> componentVariantId,
  Value<int> rowid,
});
typedef $$VariantOptionsTableTableUpdateCompanionBuilder
    = VariantOptionsTableCompanion Function({
  Value<String> id,
  Value<String> optionGroupId,
  Value<String> name,
  Value<int> displayOrder,
  Value<bool> isActive,
  Value<String?> componentVariantId,
  Value<int> rowid,
});

class $$VariantOptionsTableTableFilterComposer
    extends Composer<_$AppDatabase, $VariantOptionsTableTable> {
  $$VariantOptionsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get optionGroupId => $composableBuilder(
      column: $table.optionGroupId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get componentVariantId => $composableBuilder(
      column: $table.componentVariantId,
      builder: (column) => ColumnFilters(column));
}

class $$VariantOptionsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $VariantOptionsTableTable> {
  $$VariantOptionsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get optionGroupId => $composableBuilder(
      column: $table.optionGroupId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get componentVariantId => $composableBuilder(
      column: $table.componentVariantId,
      builder: (column) => ColumnOrderings(column));
}

class $$VariantOptionsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $VariantOptionsTableTable> {
  $$VariantOptionsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get optionGroupId => $composableBuilder(
      column: $table.optionGroupId, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => column);

  GeneratedColumn<bool> get isActive =>
      $composableBuilder(column: $table.isActive, builder: (column) => column);

  GeneratedColumn<String> get componentVariantId => $composableBuilder(
      column: $table.componentVariantId, builder: (column) => column);
}

class $$VariantOptionsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $VariantOptionsTableTable,
    VariantOptionsTableData,
    $$VariantOptionsTableTableFilterComposer,
    $$VariantOptionsTableTableOrderingComposer,
    $$VariantOptionsTableTableAnnotationComposer,
    $$VariantOptionsTableTableCreateCompanionBuilder,
    $$VariantOptionsTableTableUpdateCompanionBuilder,
    (
      VariantOptionsTableData,
      BaseReferences<_$AppDatabase, $VariantOptionsTableTable,
          VariantOptionsTableData>
    ),
    VariantOptionsTableData,
    PrefetchHooks Function()> {
  $$VariantOptionsTableTableTableManager(
      _$AppDatabase db, $VariantOptionsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$VariantOptionsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$VariantOptionsTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$VariantOptionsTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> optionGroupId = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<int> displayOrder = const Value.absent(),
            Value<bool> isActive = const Value.absent(),
            Value<String?> componentVariantId = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantOptionsTableCompanion(
            id: id,
            optionGroupId: optionGroupId,
            name: name,
            displayOrder: displayOrder,
            isActive: isActive,
            componentVariantId: componentVariantId,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String optionGroupId,
            required String name,
            required int displayOrder,
            required bool isActive,
            Value<String?> componentVariantId = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantOptionsTableCompanion.insert(
            id: id,
            optionGroupId: optionGroupId,
            name: name,
            displayOrder: displayOrder,
            isActive: isActive,
            componentVariantId: componentVariantId,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$VariantOptionsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $VariantOptionsTableTable,
    VariantOptionsTableData,
    $$VariantOptionsTableTableFilterComposer,
    $$VariantOptionsTableTableOrderingComposer,
    $$VariantOptionsTableTableAnnotationComposer,
    $$VariantOptionsTableTableCreateCompanionBuilder,
    $$VariantOptionsTableTableUpdateCompanionBuilder,
    (
      VariantOptionsTableData,
      BaseReferences<_$AppDatabase, $VariantOptionsTableTable,
          VariantOptionsTableData>
    ),
    VariantOptionsTableData,
    PrefetchHooks Function()>;
typedef $$VariantsTableTableCreateCompanionBuilder = VariantsTableCompanion
    Function({
  required String id,
  required String productId,
  required String optionValueIds,
  required String salePrice,
  Value<String?> costPrice,
  Value<String?> comparePrice,
  Value<bool> tracksInventory,
  Value<bool> isDefault,
  Value<bool> sellable,
  Value<String?> sellableReason,
  Value<bool> allowInventoryTracking,
  Value<String?> productName,
  Value<String?> variantName,
  Value<int> rowid,
});
typedef $$VariantsTableTableUpdateCompanionBuilder = VariantsTableCompanion
    Function({
  Value<String> id,
  Value<String> productId,
  Value<String> optionValueIds,
  Value<String> salePrice,
  Value<String?> costPrice,
  Value<String?> comparePrice,
  Value<bool> tracksInventory,
  Value<bool> isDefault,
  Value<bool> sellable,
  Value<String?> sellableReason,
  Value<bool> allowInventoryTracking,
  Value<String?> productName,
  Value<String?> variantName,
  Value<int> rowid,
});

class $$VariantsTableTableFilterComposer
    extends Composer<_$AppDatabase, $VariantsTableTable> {
  $$VariantsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get optionValueIds => $composableBuilder(
      column: $table.optionValueIds,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get salePrice => $composableBuilder(
      column: $table.salePrice, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get costPrice => $composableBuilder(
      column: $table.costPrice, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get comparePrice => $composableBuilder(
      column: $table.comparePrice, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get tracksInventory => $composableBuilder(
      column: $table.tracksInventory,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isDefault => $composableBuilder(
      column: $table.isDefault, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get sellable => $composableBuilder(
      column: $table.sellable, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get sellableReason => $composableBuilder(
      column: $table.sellableReason,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get allowInventoryTracking => $composableBuilder(
      column: $table.allowInventoryTracking,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get variantName => $composableBuilder(
      column: $table.variantName, builder: (column) => ColumnFilters(column));
}

class $$VariantsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $VariantsTableTable> {
  $$VariantsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get optionValueIds => $composableBuilder(
      column: $table.optionValueIds,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get salePrice => $composableBuilder(
      column: $table.salePrice, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get costPrice => $composableBuilder(
      column: $table.costPrice, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get comparePrice => $composableBuilder(
      column: $table.comparePrice,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get tracksInventory => $composableBuilder(
      column: $table.tracksInventory,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isDefault => $composableBuilder(
      column: $table.isDefault, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get sellable => $composableBuilder(
      column: $table.sellable, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get sellableReason => $composableBuilder(
      column: $table.sellableReason,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get allowInventoryTracking => $composableBuilder(
      column: $table.allowInventoryTracking,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get variantName => $composableBuilder(
      column: $table.variantName, builder: (column) => ColumnOrderings(column));
}

class $$VariantsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $VariantsTableTable> {
  $$VariantsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get optionValueIds => $composableBuilder(
      column: $table.optionValueIds, builder: (column) => column);

  GeneratedColumn<String> get salePrice =>
      $composableBuilder(column: $table.salePrice, builder: (column) => column);

  GeneratedColumn<String> get costPrice =>
      $composableBuilder(column: $table.costPrice, builder: (column) => column);

  GeneratedColumn<String> get comparePrice => $composableBuilder(
      column: $table.comparePrice, builder: (column) => column);

  GeneratedColumn<bool> get tracksInventory => $composableBuilder(
      column: $table.tracksInventory, builder: (column) => column);

  GeneratedColumn<bool> get isDefault =>
      $composableBuilder(column: $table.isDefault, builder: (column) => column);

  GeneratedColumn<bool> get sellable =>
      $composableBuilder(column: $table.sellable, builder: (column) => column);

  GeneratedColumn<String> get sellableReason => $composableBuilder(
      column: $table.sellableReason, builder: (column) => column);

  GeneratedColumn<bool> get allowInventoryTracking => $composableBuilder(
      column: $table.allowInventoryTracking, builder: (column) => column);

  GeneratedColumn<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => column);

  GeneratedColumn<String> get variantName => $composableBuilder(
      column: $table.variantName, builder: (column) => column);
}

class $$VariantsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $VariantsTableTable,
    VariantsTableData,
    $$VariantsTableTableFilterComposer,
    $$VariantsTableTableOrderingComposer,
    $$VariantsTableTableAnnotationComposer,
    $$VariantsTableTableCreateCompanionBuilder,
    $$VariantsTableTableUpdateCompanionBuilder,
    (
      VariantsTableData,
      BaseReferences<_$AppDatabase, $VariantsTableTable, VariantsTableData>
    ),
    VariantsTableData,
    PrefetchHooks Function()> {
  $$VariantsTableTableTableManager(_$AppDatabase db, $VariantsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$VariantsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$VariantsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$VariantsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> productId = const Value.absent(),
            Value<String> optionValueIds = const Value.absent(),
            Value<String> salePrice = const Value.absent(),
            Value<String?> costPrice = const Value.absent(),
            Value<String?> comparePrice = const Value.absent(),
            Value<bool> tracksInventory = const Value.absent(),
            Value<bool> isDefault = const Value.absent(),
            Value<bool> sellable = const Value.absent(),
            Value<String?> sellableReason = const Value.absent(),
            Value<bool> allowInventoryTracking = const Value.absent(),
            Value<String?> productName = const Value.absent(),
            Value<String?> variantName = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantsTableCompanion(
            id: id,
            productId: productId,
            optionValueIds: optionValueIds,
            salePrice: salePrice,
            costPrice: costPrice,
            comparePrice: comparePrice,
            tracksInventory: tracksInventory,
            isDefault: isDefault,
            sellable: sellable,
            sellableReason: sellableReason,
            allowInventoryTracking: allowInventoryTracking,
            productName: productName,
            variantName: variantName,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String productId,
            required String optionValueIds,
            required String salePrice,
            Value<String?> costPrice = const Value.absent(),
            Value<String?> comparePrice = const Value.absent(),
            Value<bool> tracksInventory = const Value.absent(),
            Value<bool> isDefault = const Value.absent(),
            Value<bool> sellable = const Value.absent(),
            Value<String?> sellableReason = const Value.absent(),
            Value<bool> allowInventoryTracking = const Value.absent(),
            Value<String?> productName = const Value.absent(),
            Value<String?> variantName = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantsTableCompanion.insert(
            id: id,
            productId: productId,
            optionValueIds: optionValueIds,
            salePrice: salePrice,
            costPrice: costPrice,
            comparePrice: comparePrice,
            tracksInventory: tracksInventory,
            isDefault: isDefault,
            sellable: sellable,
            sellableReason: sellableReason,
            allowInventoryTracking: allowInventoryTracking,
            productName: productName,
            variantName: variantName,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$VariantsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $VariantsTableTable,
    VariantsTableData,
    $$VariantsTableTableFilterComposer,
    $$VariantsTableTableOrderingComposer,
    $$VariantsTableTableAnnotationComposer,
    $$VariantsTableTableCreateCompanionBuilder,
    $$VariantsTableTableUpdateCompanionBuilder,
    (
      VariantsTableData,
      BaseReferences<_$AppDatabase, $VariantsTableTable, VariantsTableData>
    ),
    VariantsTableData,
    PrefetchHooks Function()>;
typedef $$VariantBranchStockTableTableCreateCompanionBuilder
    = VariantBranchStockTableCompanion Function({
  required String variantId,
  required String branchId,
  Value<int> quantity,
  Value<int> rowid,
});
typedef $$VariantBranchStockTableTableUpdateCompanionBuilder
    = VariantBranchStockTableCompanion Function({
  Value<String> variantId,
  Value<String> branchId,
  Value<int> quantity,
  Value<int> rowid,
});

class $$VariantBranchStockTableTableFilterComposer
    extends Composer<_$AppDatabase, $VariantBranchStockTableTable> {
  $$VariantBranchStockTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get variantId => $composableBuilder(
      column: $table.variantId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get branchId => $composableBuilder(
      column: $table.branchId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnFilters(column));
}

class $$VariantBranchStockTableTableOrderingComposer
    extends Composer<_$AppDatabase, $VariantBranchStockTableTable> {
  $$VariantBranchStockTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get variantId => $composableBuilder(
      column: $table.variantId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get branchId => $composableBuilder(
      column: $table.branchId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnOrderings(column));
}

class $$VariantBranchStockTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $VariantBranchStockTableTable> {
  $$VariantBranchStockTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get variantId =>
      $composableBuilder(column: $table.variantId, builder: (column) => column);

  GeneratedColumn<String> get branchId =>
      $composableBuilder(column: $table.branchId, builder: (column) => column);

  GeneratedColumn<int> get quantity =>
      $composableBuilder(column: $table.quantity, builder: (column) => column);
}

class $$VariantBranchStockTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $VariantBranchStockTableTable,
    VariantBranchStockTableData,
    $$VariantBranchStockTableTableFilterComposer,
    $$VariantBranchStockTableTableOrderingComposer,
    $$VariantBranchStockTableTableAnnotationComposer,
    $$VariantBranchStockTableTableCreateCompanionBuilder,
    $$VariantBranchStockTableTableUpdateCompanionBuilder,
    (
      VariantBranchStockTableData,
      BaseReferences<_$AppDatabase, $VariantBranchStockTableTable,
          VariantBranchStockTableData>
    ),
    VariantBranchStockTableData,
    PrefetchHooks Function()> {
  $$VariantBranchStockTableTableTableManager(
      _$AppDatabase db, $VariantBranchStockTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$VariantBranchStockTableTableFilterComposer(
                  $db: db, $table: table),
          createOrderingComposer: () =>
              $$VariantBranchStockTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$VariantBranchStockTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> variantId = const Value.absent(),
            Value<String> branchId = const Value.absent(),
            Value<int> quantity = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantBranchStockTableCompanion(
            variantId: variantId,
            branchId: branchId,
            quantity: quantity,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String variantId,
            required String branchId,
            Value<int> quantity = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              VariantBranchStockTableCompanion.insert(
            variantId: variantId,
            branchId: branchId,
            quantity: quantity,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$VariantBranchStockTableTableProcessedTableManager
    = ProcessedTableManager<
        _$AppDatabase,
        $VariantBranchStockTableTable,
        VariantBranchStockTableData,
        $$VariantBranchStockTableTableFilterComposer,
        $$VariantBranchStockTableTableOrderingComposer,
        $$VariantBranchStockTableTableAnnotationComposer,
        $$VariantBranchStockTableTableCreateCompanionBuilder,
        $$VariantBranchStockTableTableUpdateCompanionBuilder,
        (
          VariantBranchStockTableData,
          BaseReferences<_$AppDatabase, $VariantBranchStockTableTable,
              VariantBranchStockTableData>
        ),
        VariantBranchStockTableData,
        PrefetchHooks Function()>;
typedef $$AddonGroupsTableTableCreateCompanionBuilder
    = AddonGroupsTableCompanion Function({
  required String id,
  required String productId,
  required String name,
  required String selectionType,
  required int minSelect,
  Value<int?> maxSelect,
  required int displayOrder,
  Value<int> rowid,
});
typedef $$AddonGroupsTableTableUpdateCompanionBuilder
    = AddonGroupsTableCompanion Function({
  Value<String> id,
  Value<String> productId,
  Value<String> name,
  Value<String> selectionType,
  Value<int> minSelect,
  Value<int?> maxSelect,
  Value<int> displayOrder,
  Value<int> rowid,
});

class $$AddonGroupsTableTableFilterComposer
    extends Composer<_$AppDatabase, $AddonGroupsTableTable> {
  $$AddonGroupsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get selectionType => $composableBuilder(
      column: $table.selectionType, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get minSelect => $composableBuilder(
      column: $table.minSelect, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get maxSelect => $composableBuilder(
      column: $table.maxSelect, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => ColumnFilters(column));
}

class $$AddonGroupsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $AddonGroupsTableTable> {
  $$AddonGroupsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get selectionType => $composableBuilder(
      column: $table.selectionType,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get minSelect => $composableBuilder(
      column: $table.minSelect, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get maxSelect => $composableBuilder(
      column: $table.maxSelect, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder,
      builder: (column) => ColumnOrderings(column));
}

class $$AddonGroupsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $AddonGroupsTableTable> {
  $$AddonGroupsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get selectionType => $composableBuilder(
      column: $table.selectionType, builder: (column) => column);

  GeneratedColumn<int> get minSelect =>
      $composableBuilder(column: $table.minSelect, builder: (column) => column);

  GeneratedColumn<int> get maxSelect =>
      $composableBuilder(column: $table.maxSelect, builder: (column) => column);

  GeneratedColumn<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => column);
}

class $$AddonGroupsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $AddonGroupsTableTable,
    AddonGroupsTableData,
    $$AddonGroupsTableTableFilterComposer,
    $$AddonGroupsTableTableOrderingComposer,
    $$AddonGroupsTableTableAnnotationComposer,
    $$AddonGroupsTableTableCreateCompanionBuilder,
    $$AddonGroupsTableTableUpdateCompanionBuilder,
    (
      AddonGroupsTableData,
      BaseReferences<_$AppDatabase, $AddonGroupsTableTable,
          AddonGroupsTableData>
    ),
    AddonGroupsTableData,
    PrefetchHooks Function()> {
  $$AddonGroupsTableTableTableManager(
      _$AppDatabase db, $AddonGroupsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AddonGroupsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AddonGroupsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AddonGroupsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> productId = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String> selectionType = const Value.absent(),
            Value<int> minSelect = const Value.absent(),
            Value<int?> maxSelect = const Value.absent(),
            Value<int> displayOrder = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AddonGroupsTableCompanion(
            id: id,
            productId: productId,
            name: name,
            selectionType: selectionType,
            minSelect: minSelect,
            maxSelect: maxSelect,
            displayOrder: displayOrder,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String productId,
            required String name,
            required String selectionType,
            required int minSelect,
            Value<int?> maxSelect = const Value.absent(),
            required int displayOrder,
            Value<int> rowid = const Value.absent(),
          }) =>
              AddonGroupsTableCompanion.insert(
            id: id,
            productId: productId,
            name: name,
            selectionType: selectionType,
            minSelect: minSelect,
            maxSelect: maxSelect,
            displayOrder: displayOrder,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$AddonGroupsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $AddonGroupsTableTable,
    AddonGroupsTableData,
    $$AddonGroupsTableTableFilterComposer,
    $$AddonGroupsTableTableOrderingComposer,
    $$AddonGroupsTableTableAnnotationComposer,
    $$AddonGroupsTableTableCreateCompanionBuilder,
    $$AddonGroupsTableTableUpdateCompanionBuilder,
    (
      AddonGroupsTableData,
      BaseReferences<_$AppDatabase, $AddonGroupsTableTable,
          AddonGroupsTableData>
    ),
    AddonGroupsTableData,
    PrefetchHooks Function()>;
typedef $$AddonItemsTableTableCreateCompanionBuilder = AddonItemsTableCompanion
    Function({
  required String id,
  required String addonGroupId,
  required String name,
  required String priceDelta,
  Value<bool> defaultSelected,
  required int displayOrder,
  required bool isActive,
  Value<int> rowid,
});
typedef $$AddonItemsTableTableUpdateCompanionBuilder = AddonItemsTableCompanion
    Function({
  Value<String> id,
  Value<String> addonGroupId,
  Value<String> name,
  Value<String> priceDelta,
  Value<bool> defaultSelected,
  Value<int> displayOrder,
  Value<bool> isActive,
  Value<int> rowid,
});

class $$AddonItemsTableTableFilterComposer
    extends Composer<_$AppDatabase, $AddonItemsTableTable> {
  $$AddonItemsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get addonGroupId => $composableBuilder(
      column: $table.addonGroupId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get priceDelta => $composableBuilder(
      column: $table.priceDelta, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get defaultSelected => $composableBuilder(
      column: $table.defaultSelected,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnFilters(column));
}

class $$AddonItemsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $AddonItemsTableTable> {
  $$AddonItemsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get addonGroupId => $composableBuilder(
      column: $table.addonGroupId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get priceDelta => $composableBuilder(
      column: $table.priceDelta, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get defaultSelected => $composableBuilder(
      column: $table.defaultSelected,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnOrderings(column));
}

class $$AddonItemsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $AddonItemsTableTable> {
  $$AddonItemsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get addonGroupId => $composableBuilder(
      column: $table.addonGroupId, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get priceDelta => $composableBuilder(
      column: $table.priceDelta, builder: (column) => column);

  GeneratedColumn<bool> get defaultSelected => $composableBuilder(
      column: $table.defaultSelected, builder: (column) => column);

  GeneratedColumn<int> get displayOrder => $composableBuilder(
      column: $table.displayOrder, builder: (column) => column);

  GeneratedColumn<bool> get isActive =>
      $composableBuilder(column: $table.isActive, builder: (column) => column);
}

class $$AddonItemsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $AddonItemsTableTable,
    AddonItemsTableData,
    $$AddonItemsTableTableFilterComposer,
    $$AddonItemsTableTableOrderingComposer,
    $$AddonItemsTableTableAnnotationComposer,
    $$AddonItemsTableTableCreateCompanionBuilder,
    $$AddonItemsTableTableUpdateCompanionBuilder,
    (
      AddonItemsTableData,
      BaseReferences<_$AppDatabase, $AddonItemsTableTable, AddonItemsTableData>
    ),
    AddonItemsTableData,
    PrefetchHooks Function()> {
  $$AddonItemsTableTableTableManager(
      _$AppDatabase db, $AddonItemsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AddonItemsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AddonItemsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AddonItemsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> addonGroupId = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String> priceDelta = const Value.absent(),
            Value<bool> defaultSelected = const Value.absent(),
            Value<int> displayOrder = const Value.absent(),
            Value<bool> isActive = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AddonItemsTableCompanion(
            id: id,
            addonGroupId: addonGroupId,
            name: name,
            priceDelta: priceDelta,
            defaultSelected: defaultSelected,
            displayOrder: displayOrder,
            isActive: isActive,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String addonGroupId,
            required String name,
            required String priceDelta,
            Value<bool> defaultSelected = const Value.absent(),
            required int displayOrder,
            required bool isActive,
            Value<int> rowid = const Value.absent(),
          }) =>
              AddonItemsTableCompanion.insert(
            id: id,
            addonGroupId: addonGroupId,
            name: name,
            priceDelta: priceDelta,
            defaultSelected: defaultSelected,
            displayOrder: displayOrder,
            isActive: isActive,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$AddonItemsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $AddonItemsTableTable,
    AddonItemsTableData,
    $$AddonItemsTableTableFilterComposer,
    $$AddonItemsTableTableOrderingComposer,
    $$AddonItemsTableTableAnnotationComposer,
    $$AddonItemsTableTableCreateCompanionBuilder,
    $$AddonItemsTableTableUpdateCompanionBuilder,
    (
      AddonItemsTableData,
      BaseReferences<_$AppDatabase, $AddonItemsTableTable, AddonItemsTableData>
    ),
    AddonItemsTableData,
    PrefetchHooks Function()>;
typedef $$TaxRatesTableTableCreateCompanionBuilder = TaxRatesTableCompanion
    Function({
  required String id,
  required String name,
  required String rate,
  required bool isInclusive,
  required bool isDefault,
  Value<int> rowid,
});
typedef $$TaxRatesTableTableUpdateCompanionBuilder = TaxRatesTableCompanion
    Function({
  Value<String> id,
  Value<String> name,
  Value<String> rate,
  Value<bool> isInclusive,
  Value<bool> isDefault,
  Value<int> rowid,
});

class $$TaxRatesTableTableFilterComposer
    extends Composer<_$AppDatabase, $TaxRatesTableTable> {
  $$TaxRatesTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get rate => $composableBuilder(
      column: $table.rate, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isInclusive => $composableBuilder(
      column: $table.isInclusive, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isDefault => $composableBuilder(
      column: $table.isDefault, builder: (column) => ColumnFilters(column));
}

class $$TaxRatesTableTableOrderingComposer
    extends Composer<_$AppDatabase, $TaxRatesTableTable> {
  $$TaxRatesTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get rate => $composableBuilder(
      column: $table.rate, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isInclusive => $composableBuilder(
      column: $table.isInclusive, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isDefault => $composableBuilder(
      column: $table.isDefault, builder: (column) => ColumnOrderings(column));
}

class $$TaxRatesTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $TaxRatesTableTable> {
  $$TaxRatesTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get rate =>
      $composableBuilder(column: $table.rate, builder: (column) => column);

  GeneratedColumn<bool> get isInclusive => $composableBuilder(
      column: $table.isInclusive, builder: (column) => column);

  GeneratedColumn<bool> get isDefault =>
      $composableBuilder(column: $table.isDefault, builder: (column) => column);
}

class $$TaxRatesTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $TaxRatesTableTable,
    TaxRatesTableData,
    $$TaxRatesTableTableFilterComposer,
    $$TaxRatesTableTableOrderingComposer,
    $$TaxRatesTableTableAnnotationComposer,
    $$TaxRatesTableTableCreateCompanionBuilder,
    $$TaxRatesTableTableUpdateCompanionBuilder,
    (
      TaxRatesTableData,
      BaseReferences<_$AppDatabase, $TaxRatesTableTable, TaxRatesTableData>
    ),
    TaxRatesTableData,
    PrefetchHooks Function()> {
  $$TaxRatesTableTableTableManager(_$AppDatabase db, $TaxRatesTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$TaxRatesTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$TaxRatesTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$TaxRatesTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String> rate = const Value.absent(),
            Value<bool> isInclusive = const Value.absent(),
            Value<bool> isDefault = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              TaxRatesTableCompanion(
            id: id,
            name: name,
            rate: rate,
            isInclusive: isInclusive,
            isDefault: isDefault,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String name,
            required String rate,
            required bool isInclusive,
            required bool isDefault,
            Value<int> rowid = const Value.absent(),
          }) =>
              TaxRatesTableCompanion.insert(
            id: id,
            name: name,
            rate: rate,
            isInclusive: isInclusive,
            isDefault: isDefault,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$TaxRatesTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $TaxRatesTableTable,
    TaxRatesTableData,
    $$TaxRatesTableTableFilterComposer,
    $$TaxRatesTableTableOrderingComposer,
    $$TaxRatesTableTableAnnotationComposer,
    $$TaxRatesTableTableCreateCompanionBuilder,
    $$TaxRatesTableTableUpdateCompanionBuilder,
    (
      TaxRatesTableData,
      BaseReferences<_$AppDatabase, $TaxRatesTableTable, TaxRatesTableData>
    ),
    TaxRatesTableData,
    PrefetchHooks Function()>;
typedef $$DealsTableTableCreateCompanionBuilder = DealsTableCompanion Function({
  required String id,
  required String name,
  Value<String?> description,
  required String dealCode,
  Value<String?> fixedPrice,
  Value<String?> discountValue,
  Value<String?> discountType,
  Value<DateTime?> validFrom,
  Value<DateTime?> validUntil,
  required bool isActive,
  Value<int> rowid,
});
typedef $$DealsTableTableUpdateCompanionBuilder = DealsTableCompanion Function({
  Value<String> id,
  Value<String> name,
  Value<String?> description,
  Value<String> dealCode,
  Value<String?> fixedPrice,
  Value<String?> discountValue,
  Value<String?> discountType,
  Value<DateTime?> validFrom,
  Value<DateTime?> validUntil,
  Value<bool> isActive,
  Value<int> rowid,
});

class $$DealsTableTableFilterComposer
    extends Composer<_$AppDatabase, $DealsTableTable> {
  $$DealsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get dealCode => $composableBuilder(
      column: $table.dealCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get fixedPrice => $composableBuilder(
      column: $table.fixedPrice, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get discountValue => $composableBuilder(
      column: $table.discountValue, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get discountType => $composableBuilder(
      column: $table.discountType, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get validFrom => $composableBuilder(
      column: $table.validFrom, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get validUntil => $composableBuilder(
      column: $table.validUntil, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnFilters(column));
}

class $$DealsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $DealsTableTable> {
  $$DealsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get dealCode => $composableBuilder(
      column: $table.dealCode, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get fixedPrice => $composableBuilder(
      column: $table.fixedPrice, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get discountValue => $composableBuilder(
      column: $table.discountValue,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get discountType => $composableBuilder(
      column: $table.discountType,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get validFrom => $composableBuilder(
      column: $table.validFrom, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get validUntil => $composableBuilder(
      column: $table.validUntil, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnOrderings(column));
}

class $$DealsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $DealsTableTable> {
  $$DealsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<String> get dealCode =>
      $composableBuilder(column: $table.dealCode, builder: (column) => column);

  GeneratedColumn<String> get fixedPrice => $composableBuilder(
      column: $table.fixedPrice, builder: (column) => column);

  GeneratedColumn<String> get discountValue => $composableBuilder(
      column: $table.discountValue, builder: (column) => column);

  GeneratedColumn<String> get discountType => $composableBuilder(
      column: $table.discountType, builder: (column) => column);

  GeneratedColumn<DateTime> get validFrom =>
      $composableBuilder(column: $table.validFrom, builder: (column) => column);

  GeneratedColumn<DateTime> get validUntil => $composableBuilder(
      column: $table.validUntil, builder: (column) => column);

  GeneratedColumn<bool> get isActive =>
      $composableBuilder(column: $table.isActive, builder: (column) => column);
}

class $$DealsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $DealsTableTable,
    DealsTableData,
    $$DealsTableTableFilterComposer,
    $$DealsTableTableOrderingComposer,
    $$DealsTableTableAnnotationComposer,
    $$DealsTableTableCreateCompanionBuilder,
    $$DealsTableTableUpdateCompanionBuilder,
    (
      DealsTableData,
      BaseReferences<_$AppDatabase, $DealsTableTable, DealsTableData>
    ),
    DealsTableData,
    PrefetchHooks Function()> {
  $$DealsTableTableTableManager(_$AppDatabase db, $DealsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$DealsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$DealsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$DealsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String?> description = const Value.absent(),
            Value<String> dealCode = const Value.absent(),
            Value<String?> fixedPrice = const Value.absent(),
            Value<String?> discountValue = const Value.absent(),
            Value<String?> discountType = const Value.absent(),
            Value<DateTime?> validFrom = const Value.absent(),
            Value<DateTime?> validUntil = const Value.absent(),
            Value<bool> isActive = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              DealsTableCompanion(
            id: id,
            name: name,
            description: description,
            dealCode: dealCode,
            fixedPrice: fixedPrice,
            discountValue: discountValue,
            discountType: discountType,
            validFrom: validFrom,
            validUntil: validUntil,
            isActive: isActive,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String name,
            Value<String?> description = const Value.absent(),
            required String dealCode,
            Value<String?> fixedPrice = const Value.absent(),
            Value<String?> discountValue = const Value.absent(),
            Value<String?> discountType = const Value.absent(),
            Value<DateTime?> validFrom = const Value.absent(),
            Value<DateTime?> validUntil = const Value.absent(),
            required bool isActive,
            Value<int> rowid = const Value.absent(),
          }) =>
              DealsTableCompanion.insert(
            id: id,
            name: name,
            description: description,
            dealCode: dealCode,
            fixedPrice: fixedPrice,
            discountValue: discountValue,
            discountType: discountType,
            validFrom: validFrom,
            validUntil: validUntil,
            isActive: isActive,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$DealsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $DealsTableTable,
    DealsTableData,
    $$DealsTableTableFilterComposer,
    $$DealsTableTableOrderingComposer,
    $$DealsTableTableAnnotationComposer,
    $$DealsTableTableCreateCompanionBuilder,
    $$DealsTableTableUpdateCompanionBuilder,
    (
      DealsTableData,
      BaseReferences<_$AppDatabase, $DealsTableTable, DealsTableData>
    ),
    DealsTableData,
    PrefetchHooks Function()>;
typedef $$DealItemsTableTableCreateCompanionBuilder = DealItemsTableCompanion
    Function({
  required String id,
  required String dealId,
  Value<String?> productId,
  Value<String?> categoryId,
  required int quantity,
  required bool isFree,
  required int sortOrder,
  Value<int> rowid,
});
typedef $$DealItemsTableTableUpdateCompanionBuilder = DealItemsTableCompanion
    Function({
  Value<String> id,
  Value<String> dealId,
  Value<String?> productId,
  Value<String?> categoryId,
  Value<int> quantity,
  Value<bool> isFree,
  Value<int> sortOrder,
  Value<int> rowid,
});

class $$DealItemsTableTableFilterComposer
    extends Composer<_$AppDatabase, $DealItemsTableTable> {
  $$DealItemsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get dealId => $composableBuilder(
      column: $table.dealId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get categoryId => $composableBuilder(
      column: $table.categoryId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isFree => $composableBuilder(
      column: $table.isFree, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnFilters(column));
}

class $$DealItemsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $DealItemsTableTable> {
  $$DealItemsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get dealId => $composableBuilder(
      column: $table.dealId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get categoryId => $composableBuilder(
      column: $table.categoryId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isFree => $composableBuilder(
      column: $table.isFree, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnOrderings(column));
}

class $$DealItemsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $DealItemsTableTable> {
  $$DealItemsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get dealId =>
      $composableBuilder(column: $table.dealId, builder: (column) => column);

  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get categoryId => $composableBuilder(
      column: $table.categoryId, builder: (column) => column);

  GeneratedColumn<int> get quantity =>
      $composableBuilder(column: $table.quantity, builder: (column) => column);

  GeneratedColumn<bool> get isFree =>
      $composableBuilder(column: $table.isFree, builder: (column) => column);

  GeneratedColumn<int> get sortOrder =>
      $composableBuilder(column: $table.sortOrder, builder: (column) => column);
}

class $$DealItemsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $DealItemsTableTable,
    DealItemsTableData,
    $$DealItemsTableTableFilterComposer,
    $$DealItemsTableTableOrderingComposer,
    $$DealItemsTableTableAnnotationComposer,
    $$DealItemsTableTableCreateCompanionBuilder,
    $$DealItemsTableTableUpdateCompanionBuilder,
    (
      DealItemsTableData,
      BaseReferences<_$AppDatabase, $DealItemsTableTable, DealItemsTableData>
    ),
    DealItemsTableData,
    PrefetchHooks Function()> {
  $$DealItemsTableTableTableManager(
      _$AppDatabase db, $DealItemsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$DealItemsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$DealItemsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$DealItemsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> dealId = const Value.absent(),
            Value<String?> productId = const Value.absent(),
            Value<String?> categoryId = const Value.absent(),
            Value<int> quantity = const Value.absent(),
            Value<bool> isFree = const Value.absent(),
            Value<int> sortOrder = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              DealItemsTableCompanion(
            id: id,
            dealId: dealId,
            productId: productId,
            categoryId: categoryId,
            quantity: quantity,
            isFree: isFree,
            sortOrder: sortOrder,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String dealId,
            Value<String?> productId = const Value.absent(),
            Value<String?> categoryId = const Value.absent(),
            required int quantity,
            required bool isFree,
            required int sortOrder,
            Value<int> rowid = const Value.absent(),
          }) =>
              DealItemsTableCompanion.insert(
            id: id,
            dealId: dealId,
            productId: productId,
            categoryId: categoryId,
            quantity: quantity,
            isFree: isFree,
            sortOrder: sortOrder,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$DealItemsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $DealItemsTableTable,
    DealItemsTableData,
    $$DealItemsTableTableFilterComposer,
    $$DealItemsTableTableOrderingComposer,
    $$DealItemsTableTableAnnotationComposer,
    $$DealItemsTableTableCreateCompanionBuilder,
    $$DealItemsTableTableUpdateCompanionBuilder,
    (
      DealItemsTableData,
      BaseReferences<_$AppDatabase, $DealItemsTableTable, DealItemsTableData>
    ),
    DealItemsTableData,
    PrefetchHooks Function()>;
typedef $$PromotionsTableTableCreateCompanionBuilder = PromotionsTableCompanion
    Function({
  required String id,
  required String name,
  Value<String?> promoCode,
  required String type,
  required String discountValue,
  Value<int?> triggerMinQty,
  Value<String?> triggerMinAmount,
  Value<String?> triggerProductId,
  Value<String?> triggerCategoryId,
  Value<DateTime?> validFrom,
  Value<DateTime?> validUntil,
  Value<int?> maxUses,
  Value<int> usedCount,
  required bool isActive,
  Value<int> rowid,
});
typedef $$PromotionsTableTableUpdateCompanionBuilder = PromotionsTableCompanion
    Function({
  Value<String> id,
  Value<String> name,
  Value<String?> promoCode,
  Value<String> type,
  Value<String> discountValue,
  Value<int?> triggerMinQty,
  Value<String?> triggerMinAmount,
  Value<String?> triggerProductId,
  Value<String?> triggerCategoryId,
  Value<DateTime?> validFrom,
  Value<DateTime?> validUntil,
  Value<int?> maxUses,
  Value<int> usedCount,
  Value<bool> isActive,
  Value<int> rowid,
});

class $$PromotionsTableTableFilterComposer
    extends Composer<_$AppDatabase, $PromotionsTableTable> {
  $$PromotionsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get promoCode => $composableBuilder(
      column: $table.promoCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get type => $composableBuilder(
      column: $table.type, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get discountValue => $composableBuilder(
      column: $table.discountValue, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get triggerMinQty => $composableBuilder(
      column: $table.triggerMinQty, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get triggerMinAmount => $composableBuilder(
      column: $table.triggerMinAmount,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get triggerProductId => $composableBuilder(
      column: $table.triggerProductId,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get triggerCategoryId => $composableBuilder(
      column: $table.triggerCategoryId,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get validFrom => $composableBuilder(
      column: $table.validFrom, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get validUntil => $composableBuilder(
      column: $table.validUntil, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get maxUses => $composableBuilder(
      column: $table.maxUses, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get usedCount => $composableBuilder(
      column: $table.usedCount, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnFilters(column));
}

class $$PromotionsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $PromotionsTableTable> {
  $$PromotionsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get promoCode => $composableBuilder(
      column: $table.promoCode, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get type => $composableBuilder(
      column: $table.type, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get discountValue => $composableBuilder(
      column: $table.discountValue,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get triggerMinQty => $composableBuilder(
      column: $table.triggerMinQty,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get triggerMinAmount => $composableBuilder(
      column: $table.triggerMinAmount,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get triggerProductId => $composableBuilder(
      column: $table.triggerProductId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get triggerCategoryId => $composableBuilder(
      column: $table.triggerCategoryId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get validFrom => $composableBuilder(
      column: $table.validFrom, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get validUntil => $composableBuilder(
      column: $table.validUntil, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get maxUses => $composableBuilder(
      column: $table.maxUses, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get usedCount => $composableBuilder(
      column: $table.usedCount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isActive => $composableBuilder(
      column: $table.isActive, builder: (column) => ColumnOrderings(column));
}

class $$PromotionsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $PromotionsTableTable> {
  $$PromotionsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get promoCode =>
      $composableBuilder(column: $table.promoCode, builder: (column) => column);

  GeneratedColumn<String> get type =>
      $composableBuilder(column: $table.type, builder: (column) => column);

  GeneratedColumn<String> get discountValue => $composableBuilder(
      column: $table.discountValue, builder: (column) => column);

  GeneratedColumn<int> get triggerMinQty => $composableBuilder(
      column: $table.triggerMinQty, builder: (column) => column);

  GeneratedColumn<String> get triggerMinAmount => $composableBuilder(
      column: $table.triggerMinAmount, builder: (column) => column);

  GeneratedColumn<String> get triggerProductId => $composableBuilder(
      column: $table.triggerProductId, builder: (column) => column);

  GeneratedColumn<String> get triggerCategoryId => $composableBuilder(
      column: $table.triggerCategoryId, builder: (column) => column);

  GeneratedColumn<DateTime> get validFrom =>
      $composableBuilder(column: $table.validFrom, builder: (column) => column);

  GeneratedColumn<DateTime> get validUntil => $composableBuilder(
      column: $table.validUntil, builder: (column) => column);

  GeneratedColumn<int> get maxUses =>
      $composableBuilder(column: $table.maxUses, builder: (column) => column);

  GeneratedColumn<int> get usedCount =>
      $composableBuilder(column: $table.usedCount, builder: (column) => column);

  GeneratedColumn<bool> get isActive =>
      $composableBuilder(column: $table.isActive, builder: (column) => column);
}

class $$PromotionsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $PromotionsTableTable,
    PromotionsTableData,
    $$PromotionsTableTableFilterComposer,
    $$PromotionsTableTableOrderingComposer,
    $$PromotionsTableTableAnnotationComposer,
    $$PromotionsTableTableCreateCompanionBuilder,
    $$PromotionsTableTableUpdateCompanionBuilder,
    (
      PromotionsTableData,
      BaseReferences<_$AppDatabase, $PromotionsTableTable, PromotionsTableData>
    ),
    PromotionsTableData,
    PrefetchHooks Function()> {
  $$PromotionsTableTableTableManager(
      _$AppDatabase db, $PromotionsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PromotionsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PromotionsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PromotionsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String?> promoCode = const Value.absent(),
            Value<String> type = const Value.absent(),
            Value<String> discountValue = const Value.absent(),
            Value<int?> triggerMinQty = const Value.absent(),
            Value<String?> triggerMinAmount = const Value.absent(),
            Value<String?> triggerProductId = const Value.absent(),
            Value<String?> triggerCategoryId = const Value.absent(),
            Value<DateTime?> validFrom = const Value.absent(),
            Value<DateTime?> validUntil = const Value.absent(),
            Value<int?> maxUses = const Value.absent(),
            Value<int> usedCount = const Value.absent(),
            Value<bool> isActive = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              PromotionsTableCompanion(
            id: id,
            name: name,
            promoCode: promoCode,
            type: type,
            discountValue: discountValue,
            triggerMinQty: triggerMinQty,
            triggerMinAmount: triggerMinAmount,
            triggerProductId: triggerProductId,
            triggerCategoryId: triggerCategoryId,
            validFrom: validFrom,
            validUntil: validUntil,
            maxUses: maxUses,
            usedCount: usedCount,
            isActive: isActive,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String name,
            Value<String?> promoCode = const Value.absent(),
            required String type,
            required String discountValue,
            Value<int?> triggerMinQty = const Value.absent(),
            Value<String?> triggerMinAmount = const Value.absent(),
            Value<String?> triggerProductId = const Value.absent(),
            Value<String?> triggerCategoryId = const Value.absent(),
            Value<DateTime?> validFrom = const Value.absent(),
            Value<DateTime?> validUntil = const Value.absent(),
            Value<int?> maxUses = const Value.absent(),
            Value<int> usedCount = const Value.absent(),
            required bool isActive,
            Value<int> rowid = const Value.absent(),
          }) =>
              PromotionsTableCompanion.insert(
            id: id,
            name: name,
            promoCode: promoCode,
            type: type,
            discountValue: discountValue,
            triggerMinQty: triggerMinQty,
            triggerMinAmount: triggerMinAmount,
            triggerProductId: triggerProductId,
            triggerCategoryId: triggerCategoryId,
            validFrom: validFrom,
            validUntil: validUntil,
            maxUses: maxUses,
            usedCount: usedCount,
            isActive: isActive,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$PromotionsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $PromotionsTableTable,
    PromotionsTableData,
    $$PromotionsTableTableFilterComposer,
    $$PromotionsTableTableOrderingComposer,
    $$PromotionsTableTableAnnotationComposer,
    $$PromotionsTableTableCreateCompanionBuilder,
    $$PromotionsTableTableUpdateCompanionBuilder,
    (
      PromotionsTableData,
      BaseReferences<_$AppDatabase, $PromotionsTableTable, PromotionsTableData>
    ),
    PromotionsTableData,
    PrefetchHooks Function()>;
typedef $$LocalSalesTableTableCreateCompanionBuilder = LocalSalesTableCompanion
    Function({
  required String id,
  Value<String?> originProof,
  Value<String?> sessionId,
  Value<String?> cashierId,
  required String saleNumber,
  required DateTime soldAt,
  Value<String?> cashierName,
  Value<String> status,
  required String subtotal,
  required String discount,
  required String total,
  required String taxAmount,
  Value<String?> taxRate,
  Value<String?> promotionId,
  Value<String?> dealId,
  Value<bool> synced,
  Value<DateTime> createdAt,
  Value<bool> needsReview,
  Value<String?> syncError,
  Value<int> rowid,
});
typedef $$LocalSalesTableTableUpdateCompanionBuilder = LocalSalesTableCompanion
    Function({
  Value<String> id,
  Value<String?> originProof,
  Value<String?> sessionId,
  Value<String?> cashierId,
  Value<String> saleNumber,
  Value<DateTime> soldAt,
  Value<String?> cashierName,
  Value<String> status,
  Value<String> subtotal,
  Value<String> discount,
  Value<String> total,
  Value<String> taxAmount,
  Value<String?> taxRate,
  Value<String?> promotionId,
  Value<String?> dealId,
  Value<bool> synced,
  Value<DateTime> createdAt,
  Value<bool> needsReview,
  Value<String?> syncError,
  Value<int> rowid,
});

class $$LocalSalesTableTableFilterComposer
    extends Composer<_$AppDatabase, $LocalSalesTableTable> {
  $$LocalSalesTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get originProof => $composableBuilder(
      column: $table.originProof, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get sessionId => $composableBuilder(
      column: $table.sessionId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get cashierId => $composableBuilder(
      column: $table.cashierId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get saleNumber => $composableBuilder(
      column: $table.saleNumber, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get soldAt => $composableBuilder(
      column: $table.soldAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get cashierName => $composableBuilder(
      column: $table.cashierName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get subtotal => $composableBuilder(
      column: $table.subtotal, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get discount => $composableBuilder(
      column: $table.discount, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get total => $composableBuilder(
      column: $table.total, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get taxAmount => $composableBuilder(
      column: $table.taxAmount, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get taxRate => $composableBuilder(
      column: $table.taxRate, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get promotionId => $composableBuilder(
      column: $table.promotionId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get dealId => $composableBuilder(
      column: $table.dealId, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get needsReview => $composableBuilder(
      column: $table.needsReview, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get syncError => $composableBuilder(
      column: $table.syncError, builder: (column) => ColumnFilters(column));
}

class $$LocalSalesTableTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalSalesTableTable> {
  $$LocalSalesTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get originProof => $composableBuilder(
      column: $table.originProof, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get sessionId => $composableBuilder(
      column: $table.sessionId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get cashierId => $composableBuilder(
      column: $table.cashierId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get saleNumber => $composableBuilder(
      column: $table.saleNumber, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get soldAt => $composableBuilder(
      column: $table.soldAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get cashierName => $composableBuilder(
      column: $table.cashierName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get subtotal => $composableBuilder(
      column: $table.subtotal, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get discount => $composableBuilder(
      column: $table.discount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get total => $composableBuilder(
      column: $table.total, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get taxAmount => $composableBuilder(
      column: $table.taxAmount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get taxRate => $composableBuilder(
      column: $table.taxRate, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get promotionId => $composableBuilder(
      column: $table.promotionId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get dealId => $composableBuilder(
      column: $table.dealId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get needsReview => $composableBuilder(
      column: $table.needsReview, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get syncError => $composableBuilder(
      column: $table.syncError, builder: (column) => ColumnOrderings(column));
}

class $$LocalSalesTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalSalesTableTable> {
  $$LocalSalesTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get originProof => $composableBuilder(
      column: $table.originProof, builder: (column) => column);

  GeneratedColumn<String> get sessionId =>
      $composableBuilder(column: $table.sessionId, builder: (column) => column);

  GeneratedColumn<String> get cashierId =>
      $composableBuilder(column: $table.cashierId, builder: (column) => column);

  GeneratedColumn<String> get saleNumber => $composableBuilder(
      column: $table.saleNumber, builder: (column) => column);

  GeneratedColumn<DateTime> get soldAt =>
      $composableBuilder(column: $table.soldAt, builder: (column) => column);

  GeneratedColumn<String> get cashierName => $composableBuilder(
      column: $table.cashierName, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get subtotal =>
      $composableBuilder(column: $table.subtotal, builder: (column) => column);

  GeneratedColumn<String> get discount =>
      $composableBuilder(column: $table.discount, builder: (column) => column);

  GeneratedColumn<String> get total =>
      $composableBuilder(column: $table.total, builder: (column) => column);

  GeneratedColumn<String> get taxAmount =>
      $composableBuilder(column: $table.taxAmount, builder: (column) => column);

  GeneratedColumn<String> get taxRate =>
      $composableBuilder(column: $table.taxRate, builder: (column) => column);

  GeneratedColumn<String> get promotionId => $composableBuilder(
      column: $table.promotionId, builder: (column) => column);

  GeneratedColumn<String> get dealId =>
      $composableBuilder(column: $table.dealId, builder: (column) => column);

  GeneratedColumn<bool> get synced =>
      $composableBuilder(column: $table.synced, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<bool> get needsReview => $composableBuilder(
      column: $table.needsReview, builder: (column) => column);

  GeneratedColumn<String> get syncError =>
      $composableBuilder(column: $table.syncError, builder: (column) => column);
}

class $$LocalSalesTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalSalesTableTable,
    LocalSalesTableData,
    $$LocalSalesTableTableFilterComposer,
    $$LocalSalesTableTableOrderingComposer,
    $$LocalSalesTableTableAnnotationComposer,
    $$LocalSalesTableTableCreateCompanionBuilder,
    $$LocalSalesTableTableUpdateCompanionBuilder,
    (
      LocalSalesTableData,
      BaseReferences<_$AppDatabase, $LocalSalesTableTable, LocalSalesTableData>
    ),
    LocalSalesTableData,
    PrefetchHooks Function()> {
  $$LocalSalesTableTableTableManager(
      _$AppDatabase db, $LocalSalesTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalSalesTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalSalesTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalSalesTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String?> originProof = const Value.absent(),
            Value<String?> sessionId = const Value.absent(),
            Value<String?> cashierId = const Value.absent(),
            Value<String> saleNumber = const Value.absent(),
            Value<DateTime> soldAt = const Value.absent(),
            Value<String?> cashierName = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<String> subtotal = const Value.absent(),
            Value<String> discount = const Value.absent(),
            Value<String> total = const Value.absent(),
            Value<String> taxAmount = const Value.absent(),
            Value<String?> taxRate = const Value.absent(),
            Value<String?> promotionId = const Value.absent(),
            Value<String?> dealId = const Value.absent(),
            Value<bool> synced = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<bool> needsReview = const Value.absent(),
            Value<String?> syncError = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSalesTableCompanion(
            id: id,
            originProof: originProof,
            sessionId: sessionId,
            cashierId: cashierId,
            saleNumber: saleNumber,
            soldAt: soldAt,
            cashierName: cashierName,
            status: status,
            subtotal: subtotal,
            discount: discount,
            total: total,
            taxAmount: taxAmount,
            taxRate: taxRate,
            promotionId: promotionId,
            dealId: dealId,
            synced: synced,
            createdAt: createdAt,
            needsReview: needsReview,
            syncError: syncError,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            Value<String?> originProof = const Value.absent(),
            Value<String?> sessionId = const Value.absent(),
            Value<String?> cashierId = const Value.absent(),
            required String saleNumber,
            required DateTime soldAt,
            Value<String?> cashierName = const Value.absent(),
            Value<String> status = const Value.absent(),
            required String subtotal,
            required String discount,
            required String total,
            required String taxAmount,
            Value<String?> taxRate = const Value.absent(),
            Value<String?> promotionId = const Value.absent(),
            Value<String?> dealId = const Value.absent(),
            Value<bool> synced = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<bool> needsReview = const Value.absent(),
            Value<String?> syncError = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSalesTableCompanion.insert(
            id: id,
            originProof: originProof,
            sessionId: sessionId,
            cashierId: cashierId,
            saleNumber: saleNumber,
            soldAt: soldAt,
            cashierName: cashierName,
            status: status,
            subtotal: subtotal,
            discount: discount,
            total: total,
            taxAmount: taxAmount,
            taxRate: taxRate,
            promotionId: promotionId,
            dealId: dealId,
            synced: synced,
            createdAt: createdAt,
            needsReview: needsReview,
            syncError: syncError,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalSalesTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $LocalSalesTableTable,
    LocalSalesTableData,
    $$LocalSalesTableTableFilterComposer,
    $$LocalSalesTableTableOrderingComposer,
    $$LocalSalesTableTableAnnotationComposer,
    $$LocalSalesTableTableCreateCompanionBuilder,
    $$LocalSalesTableTableUpdateCompanionBuilder,
    (
      LocalSalesTableData,
      BaseReferences<_$AppDatabase, $LocalSalesTableTable, LocalSalesTableData>
    ),
    LocalSalesTableData,
    PrefetchHooks Function()>;
typedef $$LocalSaleItemsTableTableCreateCompanionBuilder
    = LocalSaleItemsTableCompanion Function({
  required String id,
  required String saleId,
  Value<String?> variantId,
  required String productId,
  required String productName,
  required String quantity,
  required String unitPrice,
  required String discount,
  required String total,
  Value<String?> parentItemId,
  Value<String?> satisfiesOptionGroupId,
  Value<String?> componentOptionId,
  Value<int> rowid,
});
typedef $$LocalSaleItemsTableTableUpdateCompanionBuilder
    = LocalSaleItemsTableCompanion Function({
  Value<String> id,
  Value<String> saleId,
  Value<String?> variantId,
  Value<String> productId,
  Value<String> productName,
  Value<String> quantity,
  Value<String> unitPrice,
  Value<String> discount,
  Value<String> total,
  Value<String?> parentItemId,
  Value<String?> satisfiesOptionGroupId,
  Value<String?> componentOptionId,
  Value<int> rowid,
});

class $$LocalSaleItemsTableTableFilterComposer
    extends Composer<_$AppDatabase, $LocalSaleItemsTableTable> {
  $$LocalSaleItemsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get saleId => $composableBuilder(
      column: $table.saleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get variantId => $composableBuilder(
      column: $table.variantId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get unitPrice => $composableBuilder(
      column: $table.unitPrice, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get discount => $composableBuilder(
      column: $table.discount, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get total => $composableBuilder(
      column: $table.total, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get parentItemId => $composableBuilder(
      column: $table.parentItemId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get satisfiesOptionGroupId => $composableBuilder(
      column: $table.satisfiesOptionGroupId,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get componentOptionId => $composableBuilder(
      column: $table.componentOptionId,
      builder: (column) => ColumnFilters(column));
}

class $$LocalSaleItemsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalSaleItemsTableTable> {
  $$LocalSaleItemsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get saleId => $composableBuilder(
      column: $table.saleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get variantId => $composableBuilder(
      column: $table.variantId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get unitPrice => $composableBuilder(
      column: $table.unitPrice, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get discount => $composableBuilder(
      column: $table.discount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get total => $composableBuilder(
      column: $table.total, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get parentItemId => $composableBuilder(
      column: $table.parentItemId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get satisfiesOptionGroupId => $composableBuilder(
      column: $table.satisfiesOptionGroupId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get componentOptionId => $composableBuilder(
      column: $table.componentOptionId,
      builder: (column) => ColumnOrderings(column));
}

class $$LocalSaleItemsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalSaleItemsTableTable> {
  $$LocalSaleItemsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get saleId =>
      $composableBuilder(column: $table.saleId, builder: (column) => column);

  GeneratedColumn<String> get variantId =>
      $composableBuilder(column: $table.variantId, builder: (column) => column);

  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => column);

  GeneratedColumn<String> get quantity =>
      $composableBuilder(column: $table.quantity, builder: (column) => column);

  GeneratedColumn<String> get unitPrice =>
      $composableBuilder(column: $table.unitPrice, builder: (column) => column);

  GeneratedColumn<String> get discount =>
      $composableBuilder(column: $table.discount, builder: (column) => column);

  GeneratedColumn<String> get total =>
      $composableBuilder(column: $table.total, builder: (column) => column);

  GeneratedColumn<String> get parentItemId => $composableBuilder(
      column: $table.parentItemId, builder: (column) => column);

  GeneratedColumn<String> get satisfiesOptionGroupId => $composableBuilder(
      column: $table.satisfiesOptionGroupId, builder: (column) => column);

  GeneratedColumn<String> get componentOptionId => $composableBuilder(
      column: $table.componentOptionId, builder: (column) => column);
}

class $$LocalSaleItemsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalSaleItemsTableTable,
    LocalSaleItemsTableData,
    $$LocalSaleItemsTableTableFilterComposer,
    $$LocalSaleItemsTableTableOrderingComposer,
    $$LocalSaleItemsTableTableAnnotationComposer,
    $$LocalSaleItemsTableTableCreateCompanionBuilder,
    $$LocalSaleItemsTableTableUpdateCompanionBuilder,
    (
      LocalSaleItemsTableData,
      BaseReferences<_$AppDatabase, $LocalSaleItemsTableTable,
          LocalSaleItemsTableData>
    ),
    LocalSaleItemsTableData,
    PrefetchHooks Function()> {
  $$LocalSaleItemsTableTableTableManager(
      _$AppDatabase db, $LocalSaleItemsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalSaleItemsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalSaleItemsTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalSaleItemsTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> saleId = const Value.absent(),
            Value<String?> variantId = const Value.absent(),
            Value<String> productId = const Value.absent(),
            Value<String> productName = const Value.absent(),
            Value<String> quantity = const Value.absent(),
            Value<String> unitPrice = const Value.absent(),
            Value<String> discount = const Value.absent(),
            Value<String> total = const Value.absent(),
            Value<String?> parentItemId = const Value.absent(),
            Value<String?> satisfiesOptionGroupId = const Value.absent(),
            Value<String?> componentOptionId = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSaleItemsTableCompanion(
            id: id,
            saleId: saleId,
            variantId: variantId,
            productId: productId,
            productName: productName,
            quantity: quantity,
            unitPrice: unitPrice,
            discount: discount,
            total: total,
            parentItemId: parentItemId,
            satisfiesOptionGroupId: satisfiesOptionGroupId,
            componentOptionId: componentOptionId,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String saleId,
            Value<String?> variantId = const Value.absent(),
            required String productId,
            required String productName,
            required String quantity,
            required String unitPrice,
            required String discount,
            required String total,
            Value<String?> parentItemId = const Value.absent(),
            Value<String?> satisfiesOptionGroupId = const Value.absent(),
            Value<String?> componentOptionId = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSaleItemsTableCompanion.insert(
            id: id,
            saleId: saleId,
            variantId: variantId,
            productId: productId,
            productName: productName,
            quantity: quantity,
            unitPrice: unitPrice,
            discount: discount,
            total: total,
            parentItemId: parentItemId,
            satisfiesOptionGroupId: satisfiesOptionGroupId,
            componentOptionId: componentOptionId,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalSaleItemsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $LocalSaleItemsTableTable,
    LocalSaleItemsTableData,
    $$LocalSaleItemsTableTableFilterComposer,
    $$LocalSaleItemsTableTableOrderingComposer,
    $$LocalSaleItemsTableTableAnnotationComposer,
    $$LocalSaleItemsTableTableCreateCompanionBuilder,
    $$LocalSaleItemsTableTableUpdateCompanionBuilder,
    (
      LocalSaleItemsTableData,
      BaseReferences<_$AppDatabase, $LocalSaleItemsTableTable,
          LocalSaleItemsTableData>
    ),
    LocalSaleItemsTableData,
    PrefetchHooks Function()>;
typedef $$LocalSaleItemOptionsTableTableCreateCompanionBuilder
    = LocalSaleItemOptionsTableCompanion Function({
  required String id,
  required String saleItemId,
  required String variantOptionId,
  required String optionName,
  required String priceAdjustment,
  Value<int> rowid,
});
typedef $$LocalSaleItemOptionsTableTableUpdateCompanionBuilder
    = LocalSaleItemOptionsTableCompanion Function({
  Value<String> id,
  Value<String> saleItemId,
  Value<String> variantOptionId,
  Value<String> optionName,
  Value<String> priceAdjustment,
  Value<int> rowid,
});

class $$LocalSaleItemOptionsTableTableFilterComposer
    extends Composer<_$AppDatabase, $LocalSaleItemOptionsTableTable> {
  $$LocalSaleItemOptionsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get saleItemId => $composableBuilder(
      column: $table.saleItemId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get variantOptionId => $composableBuilder(
      column: $table.variantOptionId,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get optionName => $composableBuilder(
      column: $table.optionName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get priceAdjustment => $composableBuilder(
      column: $table.priceAdjustment,
      builder: (column) => ColumnFilters(column));
}

class $$LocalSaleItemOptionsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalSaleItemOptionsTableTable> {
  $$LocalSaleItemOptionsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get saleItemId => $composableBuilder(
      column: $table.saleItemId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get variantOptionId => $composableBuilder(
      column: $table.variantOptionId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get optionName => $composableBuilder(
      column: $table.optionName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get priceAdjustment => $composableBuilder(
      column: $table.priceAdjustment,
      builder: (column) => ColumnOrderings(column));
}

class $$LocalSaleItemOptionsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalSaleItemOptionsTableTable> {
  $$LocalSaleItemOptionsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get saleItemId => $composableBuilder(
      column: $table.saleItemId, builder: (column) => column);

  GeneratedColumn<String> get variantOptionId => $composableBuilder(
      column: $table.variantOptionId, builder: (column) => column);

  GeneratedColumn<String> get optionName => $composableBuilder(
      column: $table.optionName, builder: (column) => column);

  GeneratedColumn<String> get priceAdjustment => $composableBuilder(
      column: $table.priceAdjustment, builder: (column) => column);
}

class $$LocalSaleItemOptionsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalSaleItemOptionsTableTable,
    LocalSaleItemOptionsTableData,
    $$LocalSaleItemOptionsTableTableFilterComposer,
    $$LocalSaleItemOptionsTableTableOrderingComposer,
    $$LocalSaleItemOptionsTableTableAnnotationComposer,
    $$LocalSaleItemOptionsTableTableCreateCompanionBuilder,
    $$LocalSaleItemOptionsTableTableUpdateCompanionBuilder,
    (
      LocalSaleItemOptionsTableData,
      BaseReferences<_$AppDatabase, $LocalSaleItemOptionsTableTable,
          LocalSaleItemOptionsTableData>
    ),
    LocalSaleItemOptionsTableData,
    PrefetchHooks Function()> {
  $$LocalSaleItemOptionsTableTableTableManager(
      _$AppDatabase db, $LocalSaleItemOptionsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalSaleItemOptionsTableTableFilterComposer(
                  $db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalSaleItemOptionsTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalSaleItemOptionsTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> saleItemId = const Value.absent(),
            Value<String> variantOptionId = const Value.absent(),
            Value<String> optionName = const Value.absent(),
            Value<String> priceAdjustment = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSaleItemOptionsTableCompanion(
            id: id,
            saleItemId: saleItemId,
            variantOptionId: variantOptionId,
            optionName: optionName,
            priceAdjustment: priceAdjustment,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String saleItemId,
            required String variantOptionId,
            required String optionName,
            required String priceAdjustment,
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSaleItemOptionsTableCompanion.insert(
            id: id,
            saleItemId: saleItemId,
            variantOptionId: variantOptionId,
            optionName: optionName,
            priceAdjustment: priceAdjustment,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalSaleItemOptionsTableTableProcessedTableManager
    = ProcessedTableManager<
        _$AppDatabase,
        $LocalSaleItemOptionsTableTable,
        LocalSaleItemOptionsTableData,
        $$LocalSaleItemOptionsTableTableFilterComposer,
        $$LocalSaleItemOptionsTableTableOrderingComposer,
        $$LocalSaleItemOptionsTableTableAnnotationComposer,
        $$LocalSaleItemOptionsTableTableCreateCompanionBuilder,
        $$LocalSaleItemOptionsTableTableUpdateCompanionBuilder,
        (
          LocalSaleItemOptionsTableData,
          BaseReferences<_$AppDatabase, $LocalSaleItemOptionsTableTable,
              LocalSaleItemOptionsTableData>
        ),
        LocalSaleItemOptionsTableData,
        PrefetchHooks Function()>;
typedef $$LocalSaleItemAddonsTableTableCreateCompanionBuilder
    = LocalSaleItemAddonsTableCompanion Function({
  required String id,
  required String saleItemId,
  required String addonItemId,
  required String addonName,
  required String priceDelta,
  Value<bool> wasRemoved,
  Value<int> rowid,
});
typedef $$LocalSaleItemAddonsTableTableUpdateCompanionBuilder
    = LocalSaleItemAddonsTableCompanion Function({
  Value<String> id,
  Value<String> saleItemId,
  Value<String> addonItemId,
  Value<String> addonName,
  Value<String> priceDelta,
  Value<bool> wasRemoved,
  Value<int> rowid,
});

class $$LocalSaleItemAddonsTableTableFilterComposer
    extends Composer<_$AppDatabase, $LocalSaleItemAddonsTableTable> {
  $$LocalSaleItemAddonsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get saleItemId => $composableBuilder(
      column: $table.saleItemId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get addonItemId => $composableBuilder(
      column: $table.addonItemId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get addonName => $composableBuilder(
      column: $table.addonName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get priceDelta => $composableBuilder(
      column: $table.priceDelta, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get wasRemoved => $composableBuilder(
      column: $table.wasRemoved, builder: (column) => ColumnFilters(column));
}

class $$LocalSaleItemAddonsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalSaleItemAddonsTableTable> {
  $$LocalSaleItemAddonsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get saleItemId => $composableBuilder(
      column: $table.saleItemId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get addonItemId => $composableBuilder(
      column: $table.addonItemId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get addonName => $composableBuilder(
      column: $table.addonName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get priceDelta => $composableBuilder(
      column: $table.priceDelta, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get wasRemoved => $composableBuilder(
      column: $table.wasRemoved, builder: (column) => ColumnOrderings(column));
}

class $$LocalSaleItemAddonsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalSaleItemAddonsTableTable> {
  $$LocalSaleItemAddonsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get saleItemId => $composableBuilder(
      column: $table.saleItemId, builder: (column) => column);

  GeneratedColumn<String> get addonItemId => $composableBuilder(
      column: $table.addonItemId, builder: (column) => column);

  GeneratedColumn<String> get addonName =>
      $composableBuilder(column: $table.addonName, builder: (column) => column);

  GeneratedColumn<String> get priceDelta => $composableBuilder(
      column: $table.priceDelta, builder: (column) => column);

  GeneratedColumn<bool> get wasRemoved => $composableBuilder(
      column: $table.wasRemoved, builder: (column) => column);
}

class $$LocalSaleItemAddonsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalSaleItemAddonsTableTable,
    LocalSaleItemAddonsTableData,
    $$LocalSaleItemAddonsTableTableFilterComposer,
    $$LocalSaleItemAddonsTableTableOrderingComposer,
    $$LocalSaleItemAddonsTableTableAnnotationComposer,
    $$LocalSaleItemAddonsTableTableCreateCompanionBuilder,
    $$LocalSaleItemAddonsTableTableUpdateCompanionBuilder,
    (
      LocalSaleItemAddonsTableData,
      BaseReferences<_$AppDatabase, $LocalSaleItemAddonsTableTable,
          LocalSaleItemAddonsTableData>
    ),
    LocalSaleItemAddonsTableData,
    PrefetchHooks Function()> {
  $$LocalSaleItemAddonsTableTableTableManager(
      _$AppDatabase db, $LocalSaleItemAddonsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalSaleItemAddonsTableTableFilterComposer(
                  $db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalSaleItemAddonsTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalSaleItemAddonsTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> saleItemId = const Value.absent(),
            Value<String> addonItemId = const Value.absent(),
            Value<String> addonName = const Value.absent(),
            Value<String> priceDelta = const Value.absent(),
            Value<bool> wasRemoved = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSaleItemAddonsTableCompanion(
            id: id,
            saleItemId: saleItemId,
            addonItemId: addonItemId,
            addonName: addonName,
            priceDelta: priceDelta,
            wasRemoved: wasRemoved,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String saleItemId,
            required String addonItemId,
            required String addonName,
            required String priceDelta,
            Value<bool> wasRemoved = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalSaleItemAddonsTableCompanion.insert(
            id: id,
            saleItemId: saleItemId,
            addonItemId: addonItemId,
            addonName: addonName,
            priceDelta: priceDelta,
            wasRemoved: wasRemoved,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalSaleItemAddonsTableTableProcessedTableManager
    = ProcessedTableManager<
        _$AppDatabase,
        $LocalSaleItemAddonsTableTable,
        LocalSaleItemAddonsTableData,
        $$LocalSaleItemAddonsTableTableFilterComposer,
        $$LocalSaleItemAddonsTableTableOrderingComposer,
        $$LocalSaleItemAddonsTableTableAnnotationComposer,
        $$LocalSaleItemAddonsTableTableCreateCompanionBuilder,
        $$LocalSaleItemAddonsTableTableUpdateCompanionBuilder,
        (
          LocalSaleItemAddonsTableData,
          BaseReferences<_$AppDatabase, $LocalSaleItemAddonsTableTable,
              LocalSaleItemAddonsTableData>
        ),
        LocalSaleItemAddonsTableData,
        PrefetchHooks Function()>;
typedef $$LocalPaymentsTableTableCreateCompanionBuilder
    = LocalPaymentsTableCompanion Function({
  required String id,
  required String saleId,
  required String paymentMethod,
  required String amount,
  Value<String?> reference,
  Value<int> rowid,
});
typedef $$LocalPaymentsTableTableUpdateCompanionBuilder
    = LocalPaymentsTableCompanion Function({
  Value<String> id,
  Value<String> saleId,
  Value<String> paymentMethod,
  Value<String> amount,
  Value<String?> reference,
  Value<int> rowid,
});

class $$LocalPaymentsTableTableFilterComposer
    extends Composer<_$AppDatabase, $LocalPaymentsTableTable> {
  $$LocalPaymentsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get saleId => $composableBuilder(
      column: $table.saleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get paymentMethod => $composableBuilder(
      column: $table.paymentMethod, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get amount => $composableBuilder(
      column: $table.amount, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get reference => $composableBuilder(
      column: $table.reference, builder: (column) => ColumnFilters(column));
}

class $$LocalPaymentsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalPaymentsTableTable> {
  $$LocalPaymentsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get saleId => $composableBuilder(
      column: $table.saleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get paymentMethod => $composableBuilder(
      column: $table.paymentMethod,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get amount => $composableBuilder(
      column: $table.amount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get reference => $composableBuilder(
      column: $table.reference, builder: (column) => ColumnOrderings(column));
}

class $$LocalPaymentsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalPaymentsTableTable> {
  $$LocalPaymentsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get saleId =>
      $composableBuilder(column: $table.saleId, builder: (column) => column);

  GeneratedColumn<String> get paymentMethod => $composableBuilder(
      column: $table.paymentMethod, builder: (column) => column);

  GeneratedColumn<String> get amount =>
      $composableBuilder(column: $table.amount, builder: (column) => column);

  GeneratedColumn<String> get reference =>
      $composableBuilder(column: $table.reference, builder: (column) => column);
}

class $$LocalPaymentsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalPaymentsTableTable,
    LocalPaymentsTableData,
    $$LocalPaymentsTableTableFilterComposer,
    $$LocalPaymentsTableTableOrderingComposer,
    $$LocalPaymentsTableTableAnnotationComposer,
    $$LocalPaymentsTableTableCreateCompanionBuilder,
    $$LocalPaymentsTableTableUpdateCompanionBuilder,
    (
      LocalPaymentsTableData,
      BaseReferences<_$AppDatabase, $LocalPaymentsTableTable,
          LocalPaymentsTableData>
    ),
    LocalPaymentsTableData,
    PrefetchHooks Function()> {
  $$LocalPaymentsTableTableTableManager(
      _$AppDatabase db, $LocalPaymentsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalPaymentsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalPaymentsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalPaymentsTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> saleId = const Value.absent(),
            Value<String> paymentMethod = const Value.absent(),
            Value<String> amount = const Value.absent(),
            Value<String?> reference = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalPaymentsTableCompanion(
            id: id,
            saleId: saleId,
            paymentMethod: paymentMethod,
            amount: amount,
            reference: reference,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String saleId,
            required String paymentMethod,
            required String amount,
            Value<String?> reference = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalPaymentsTableCompanion.insert(
            id: id,
            saleId: saleId,
            paymentMethod: paymentMethod,
            amount: amount,
            reference: reference,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalPaymentsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $LocalPaymentsTableTable,
    LocalPaymentsTableData,
    $$LocalPaymentsTableTableFilterComposer,
    $$LocalPaymentsTableTableOrderingComposer,
    $$LocalPaymentsTableTableAnnotationComposer,
    $$LocalPaymentsTableTableCreateCompanionBuilder,
    $$LocalPaymentsTableTableUpdateCompanionBuilder,
    (
      LocalPaymentsTableData,
      BaseReferences<_$AppDatabase, $LocalPaymentsTableTable,
          LocalPaymentsTableData>
    ),
    LocalPaymentsTableData,
    PrefetchHooks Function()>;
typedef $$LocalProductStockTableTableCreateCompanionBuilder
    = LocalProductStockTableCompanion Function({
  required String productId,
  required String quantity,
  Value<int> rowid,
});
typedef $$LocalProductStockTableTableUpdateCompanionBuilder
    = LocalProductStockTableCompanion Function({
  Value<String> productId,
  Value<String> quantity,
  Value<int> rowid,
});

class $$LocalProductStockTableTableFilterComposer
    extends Composer<_$AppDatabase, $LocalProductStockTableTable> {
  $$LocalProductStockTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnFilters(column));
}

class $$LocalProductStockTableTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalProductStockTableTable> {
  $$LocalProductStockTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnOrderings(column));
}

class $$LocalProductStockTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalProductStockTableTable> {
  $$LocalProductStockTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get quantity =>
      $composableBuilder(column: $table.quantity, builder: (column) => column);
}

class $$LocalProductStockTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalProductStockTableTable,
    LocalProductStockTableData,
    $$LocalProductStockTableTableFilterComposer,
    $$LocalProductStockTableTableOrderingComposer,
    $$LocalProductStockTableTableAnnotationComposer,
    $$LocalProductStockTableTableCreateCompanionBuilder,
    $$LocalProductStockTableTableUpdateCompanionBuilder,
    (
      LocalProductStockTableData,
      BaseReferences<_$AppDatabase, $LocalProductStockTableTable,
          LocalProductStockTableData>
    ),
    LocalProductStockTableData,
    PrefetchHooks Function()> {
  $$LocalProductStockTableTableTableManager(
      _$AppDatabase db, $LocalProductStockTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalProductStockTableTableFilterComposer(
                  $db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalProductStockTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalProductStockTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> productId = const Value.absent(),
            Value<String> quantity = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalProductStockTableCompanion(
            productId: productId,
            quantity: quantity,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String productId,
            required String quantity,
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalProductStockTableCompanion.insert(
            productId: productId,
            quantity: quantity,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalProductStockTableTableProcessedTableManager
    = ProcessedTableManager<
        _$AppDatabase,
        $LocalProductStockTableTable,
        LocalProductStockTableData,
        $$LocalProductStockTableTableFilterComposer,
        $$LocalProductStockTableTableOrderingComposer,
        $$LocalProductStockTableTableAnnotationComposer,
        $$LocalProductStockTableTableCreateCompanionBuilder,
        $$LocalProductStockTableTableUpdateCompanionBuilder,
        (
          LocalProductStockTableData,
          BaseReferences<_$AppDatabase, $LocalProductStockTableTable,
              LocalProductStockTableData>
        ),
        LocalProductStockTableData,
        PrefetchHooks Function()>;
typedef $$AppSettingsTableTableCreateCompanionBuilder
    = AppSettingsTableCompanion Function({
  required String key,
  required String value,
  Value<int> rowid,
});
typedef $$AppSettingsTableTableUpdateCompanionBuilder
    = AppSettingsTableCompanion Function({
  Value<String> key,
  Value<String> value,
  Value<int> rowid,
});

class $$AppSettingsTableTableFilterComposer
    extends Composer<_$AppDatabase, $AppSettingsTableTable> {
  $$AppSettingsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnFilters(column));
}

class $$AppSettingsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $AppSettingsTableTable> {
  $$AppSettingsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnOrderings(column));
}

class $$AppSettingsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $AppSettingsTableTable> {
  $$AppSettingsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$AppSettingsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $AppSettingsTableTable,
    AppSettingsTableData,
    $$AppSettingsTableTableFilterComposer,
    $$AppSettingsTableTableOrderingComposer,
    $$AppSettingsTableTableAnnotationComposer,
    $$AppSettingsTableTableCreateCompanionBuilder,
    $$AppSettingsTableTableUpdateCompanionBuilder,
    (
      AppSettingsTableData,
      BaseReferences<_$AppDatabase, $AppSettingsTableTable,
          AppSettingsTableData>
    ),
    AppSettingsTableData,
    PrefetchHooks Function()> {
  $$AppSettingsTableTableTableManager(
      _$AppDatabase db, $AppSettingsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AppSettingsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AppSettingsTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AppSettingsTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> key = const Value.absent(),
            Value<String> value = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AppSettingsTableCompanion(
            key: key,
            value: value,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String key,
            required String value,
            Value<int> rowid = const Value.absent(),
          }) =>
              AppSettingsTableCompanion.insert(
            key: key,
            value: value,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$AppSettingsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $AppSettingsTableTable,
    AppSettingsTableData,
    $$AppSettingsTableTableFilterComposer,
    $$AppSettingsTableTableOrderingComposer,
    $$AppSettingsTableTableAnnotationComposer,
    $$AppSettingsTableTableCreateCompanionBuilder,
    $$AppSettingsTableTableUpdateCompanionBuilder,
    (
      AppSettingsTableData,
      BaseReferences<_$AppDatabase, $AppSettingsTableTable,
          AppSettingsTableData>
    ),
    AppSettingsTableData,
    PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$CategoriesTableTableTableManager get categoriesTable =>
      $$CategoriesTableTableTableManager(_db, _db.categoriesTable);
  $$ProductsTableTableTableManager get productsTable =>
      $$ProductsTableTableTableManager(_db, _db.productsTable);
  $$VariantOptionGroupsTableTableTableManager get variantOptionGroupsTable =>
      $$VariantOptionGroupsTableTableTableManager(
          _db, _db.variantOptionGroupsTable);
  $$VariantOptionsTableTableTableManager get variantOptionsTable =>
      $$VariantOptionsTableTableTableManager(_db, _db.variantOptionsTable);
  $$VariantsTableTableTableManager get variantsTable =>
      $$VariantsTableTableTableManager(_db, _db.variantsTable);
  $$VariantBranchStockTableTableTableManager get variantBranchStockTable =>
      $$VariantBranchStockTableTableTableManager(
          _db, _db.variantBranchStockTable);
  $$AddonGroupsTableTableTableManager get addonGroupsTable =>
      $$AddonGroupsTableTableTableManager(_db, _db.addonGroupsTable);
  $$AddonItemsTableTableTableManager get addonItemsTable =>
      $$AddonItemsTableTableTableManager(_db, _db.addonItemsTable);
  $$TaxRatesTableTableTableManager get taxRatesTable =>
      $$TaxRatesTableTableTableManager(_db, _db.taxRatesTable);
  $$DealsTableTableTableManager get dealsTable =>
      $$DealsTableTableTableManager(_db, _db.dealsTable);
  $$DealItemsTableTableTableManager get dealItemsTable =>
      $$DealItemsTableTableTableManager(_db, _db.dealItemsTable);
  $$PromotionsTableTableTableManager get promotionsTable =>
      $$PromotionsTableTableTableManager(_db, _db.promotionsTable);
  $$LocalSalesTableTableTableManager get localSalesTable =>
      $$LocalSalesTableTableTableManager(_db, _db.localSalesTable);
  $$LocalSaleItemsTableTableTableManager get localSaleItemsTable =>
      $$LocalSaleItemsTableTableTableManager(_db, _db.localSaleItemsTable);
  $$LocalSaleItemOptionsTableTableTableManager get localSaleItemOptionsTable =>
      $$LocalSaleItemOptionsTableTableTableManager(
          _db, _db.localSaleItemOptionsTable);
  $$LocalSaleItemAddonsTableTableTableManager get localSaleItemAddonsTable =>
      $$LocalSaleItemAddonsTableTableTableManager(
          _db, _db.localSaleItemAddonsTable);
  $$LocalPaymentsTableTableTableManager get localPaymentsTable =>
      $$LocalPaymentsTableTableTableManager(_db, _db.localPaymentsTable);
  $$LocalProductStockTableTableTableManager get localProductStockTable =>
      $$LocalProductStockTableTableTableManager(
          _db, _db.localProductStockTable);
  $$AppSettingsTableTableTableManager get appSettingsTable =>
      $$AppSettingsTableTableTableManager(_db, _db.appSettingsTable);
}
