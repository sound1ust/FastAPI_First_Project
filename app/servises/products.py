from typing import Union, List

from asyncpg import UniqueViolationError
from pydantic import PositiveInt

from app.models.products import Product
from app.repositories.products import ProductRepository
from app.models.exceptions import (
    ProductNotFoundException,
    ProductsListNotFoundException,
    ProductNotCreatedException, ProductExistsException,
)


class ProductService(ProductRepository):  # ProductPostgresqlRepository
    async def create(self, name, category, price) -> Union[Product, None]:
        """
        Takes arguments, makes an INSERT request to a Database
        and returns a Product object or None
        """
        query = '''
        INSERT INTO products(name, category, price)
        VALUES ($1, $2, $3)
        RETURNING *;
        '''
        try:
            stored_data = await self.conn.fetchrow(
                query, name, category, price,
            )
        except UniqueViolationError as exc:
            raise ProductExistsException(name=name)

        if not stored_data:
            raise ProductNotCreatedException()

        product = self.get_product_object(stored_data)
        return product

    async def get(self, product_id: PositiveInt) -> Union[Product, None]:
        """
        Takes product_id, makes a SELECT request to a Database
        and returns a Product object or None
        """
        query = '''
        SELECT product_id, name, category, price
        FROM products
        WHERE product_id = $1;
        '''
        stored_data = await self.conn.fetchrow(query, product_id)
        if not stored_data:
            raise ProductNotFoundException(product_id=product_id)

        product = self.get_product_object(stored_data)
        return product

    async def list(
            self,
            keyword,
            category,
            limit,
    ) -> Union[List[Product], None]:
        """
        Takes arguments, makes a SELECT request to a Database
        and returns a List of a Product objects or None
        """
        params = ["%" + keyword + "%"]
        query = '''
        SELECT * FROM products 
        WHERE name ILIKE $1
        '''

        if category:
            query += '''
            AND category = $2
            '''
            params.append(category)

        query += '''
        ORDER BY product_id
        '''

        if limit:
            query += f'''
            LIMIT ${str(len(params) + 1)}
            '''
            params.append(limit)

        query += ";"

        stored_data = await self.conn.fetch(query, *params)
        if not stored_data:
            raise ProductsListNotFoundException()

        products = list(map(self.get_product_object, stored_data))
        return products

    async def update(
            self,
            product_id: PositiveInt,
            name,
            category,
            price,
    ) -> Union[Product, None]:
        """
        Takes product_id, makes an UPDATE request to a Database
        and returns a Product object or None
        """
        query = '''
        UPDATE products
        SET name = $1, category = $2, price = $3
        WHERE product_id = $4
        RETURNING *;
        '''
        try:
            stored_data = await self.conn.fetchrow(
                query, name, category, price, product_id,
            )
        except UniqueViolationError as exc:
            raise ProductExistsException(name=name)

        if not stored_data:
            raise ProductNotFoundException(product_id=product_id)

        changed_product = self.get_product_object(stored_data)
        return changed_product

    async def delete(self, product_id: PositiveInt) -> Union[Product, None]:
        """
        Takes product_id, makes a DELETE request to a Database
        and returns a Product object or None
        """
        query = '''
        DELETE FROM products WHERE product_id = $1 RETURNING *;
        '''
        stored_data = await self.conn.fetchrow(query, product_id)
        if not stored_data:
            raise ProductNotFoundException(product_id=product_id)

        deleted_product = self.get_product_object(stored_data)
        return deleted_product

    @staticmethod
    def get_product_object(stored_data) -> Product:
        return Product(**{key: value for key, value in stored_data.items()})
