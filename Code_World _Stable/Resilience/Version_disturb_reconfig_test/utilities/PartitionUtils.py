from math import *


"""
输入要分隔区域个数
以及区域的定点坐标[左下，左上，右上，右下]顺序
输出每个分隔小小块的坐标
"""


class QuadPartitioner_by_coord:
    @staticmethod
    def get_factors(number):
        """
        Takes a number and returns a list of factors
        :param number: The number for which to find the factors
        :return: a list of factors for the given number
        """
        facts = []
        for i in range(1, number + 1):
            if number % i == 0:
                facts.append(i)
                if number / i == i:
                    facts.append(i)
        return facts

    @staticmethod
    def get_partitions(N, coord):
        """
        Given a width and height, partition the area into N parts
        :param N: The number of partitions to generate
        :param quad_width: The width of the quadrilateral
        :param quad_height: The height of the quadrilateral
        :return: a list of a list of cells where each cell is defined as a list of 5 verticies
        """
        bias = coord[0]
        quad_width, quad_height = coord[2][0] - coord[0][0], coord[1][1] - coord[0][1]

        # We reverse only because my brain feels more comfortable looking at a grid in this way
        factors = list(reversed(QuadPartitioner_by_coord.get_factors(N)))

        # We need to find the middle of the factors so that we get cells
        # with as close to equal width and heights as possible
        factor_count = len(factors)

        if factor_count % 2 == 0:
            split = int(factor_count / 2)
            factors = factors[split - 1 : split + 1]
        else:
            factors = []
            split = ceil(factor_count / 2)
            factors.append(split)
            factors.append(split)

        # The width and height of an individual cell
        cell_width = quad_width / factors[0]
        cell_height = quad_height / factors[1]

        number_of_cells_in_a_row = factors[0]
        rows = factors[1]
        row_of_cells = []

        # We build just a single row of cells
        # then for each additional row, we just duplicate this row and offset the cells
        for n in range(0, number_of_cells_in_a_row):
            cell_points = []

            for i in range(0, 5):
                cell_y = 0
                cell_x = n * cell_width

                if i == 2 or i == 3:
                    cell_x = n * cell_width + cell_width

                if i == 1 or i == 2:
                    cell_y = cell_height

                cell_points.append((cell_x + bias[0], cell_y + bias[1]))

            row_of_cells.append(cell_points)

        rows_of_cells = [row_of_cells]

        # With that 1 row of cells constructed, we can simply duplicate it and offset it
        # by the height of a cell multiplied by the row number
        for index in range(1, rows):
            new_row_of_cells = [
                [(point[0], point[1] + cell_height * index) for point in square]
                for square in row_of_cells
            ]
            rows_of_cells.append(new_row_of_cells)

        return rows_of_cells
