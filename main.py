import requests
import pprint
import json
import statistics
import copy


key = "KEBTK9YOL2V0RQ61U1VG"
secret = "bMDq0IY6QlAPR31qTLseG8G2oGR3Sb0DwpxnqPNW"


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


def make_request(method, url, data=None, headers=None):
    # Set the request method
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, data=data, headers=headers)
    elif method == "PUT":
        response = requests.put(url, data=data, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError("Invalid HTTP method")

    # Return the response
    return response


def get_bybit_usdt_perps():
    # if usdt-perpetual-futures at the end of route then add
    bybit_usdt_perps = []

    response = make_request("GET", "https://api.cryptowat.ch/markets/bybit")
    response_data = response.json()['result']

    for i in response_data:
        if i['route'].endswith('usdt-perpetual-futures'):
            bybit_usdt_perps.append(i)

    return bybit_usdt_perps


def get_price_history(url):
    response = make_request("GET",
                            str(url))
    return response.json()['result']['14400']


# def get_200_ema(current_close, end):
#     multiplier = (2 / (200 + 1))
#     if end == True:
#         return (current_close * multiplier) + (current_close * (1-multiplier))
#     else:
#         return (current_close * multiplier) + (get_200_ema() * (1-multiplier))

# def get_200_ema_list_old(OHLC_list):
#     for i in reversed(OHLC_list):
#         print(candle)
#         if i==0:
#
#         get_200_ema()
#
# def get_200_ema_list(OHLC_list):
#     multiplier = (2 / (200 + 1))
#     if not OHLC_list:  # base case: empty list
#         return 0.000000000001
#     else:
#         return (OHLC_list[-1] * multiplier) + get_200_ema_list(OHLC_list[1:])

def get_200ema_list(ohlc_list):
    multiplier = (2 / (200 + 1))
    result = []
    for i in range(len(ohlc_list)):
        if i == 0:  # just put the first candle as the 200ema start
            result.append(ohlc_list[i][4])
        else:
            result.append((ohlc_list[i][4] * multiplier) + (result[i - 1] * (1 - multiplier)))
    return result


def calculate_200ema(ohlc_list):  # has 200 less datapoints
    close_prices = [candle[4] for candle in ohlc_list]

    # Calculate the simple moving average of the closing prices for the first 200 days
    sma = sum(close_prices[:200]) / 200

    # Calculate the weighting multiplier
    multiplier = 2 / (200 + 1)

    # Initialize the list of EMAs with the first SMA value
    emas = [sma]

    # Calculate the EMA for each day, starting from the 201st day
    for i in range(200, len(close_prices)):
        emas.append((close_prices[i] * multiplier) + (emas[-1] * (1 - multiplier)))

    return emas


def get_difference_price_and_200ema(ohlc_list, ema200_list, ohlc_index):
    result = []
    for i in range(len(ohlc_list)):
        result.append(ohlc_list[i][ohlc_index] - ema200_list[i])
    return result


def get_percentage_difference_price(price_difference_list, ohlc_list, ohlc_index):
    result = []
    for i in range(len(ohlc_list)):
        result.append(price_difference_list[i]/ohlc_list[i][ohlc_index]*100)
    return result


def replace_percentage_price(threshold, price_difference_percentage):
    result = []
    for i in price_difference_percentage:
        if i < threshold and i > -threshold:
            result.append(i)
        else:
            result.append(101)
    return result


def remove_replaced_percentage_price(single_clustered_price_list):
    result = []
    for i in single_clustered_price_list:
        if i != 101:
            result.append((i))
    return result


def create_array_of_array(single_clustered_price_list):
    result = []
    cluster = []
    count = 0
    for i in single_clustered_price_list:
        count = count+1
        if i != 101:
            cluster.append(i)
        if count == len(single_clustered_price_list):  # if at the end of the list then end the cluster
            if len(cluster) != 0:
                result.append(cluster)
            cluster = []
        if i == 101:  # end of cluster
            if len(cluster) != 0:
                result.append(cluster)
            cluster = []

    return result


def make_list_absolute(numbers):
    return [abs(number) for number in numbers]


def average_of_list(numbers):
    return sum(numbers) / len(numbers)


def remove_negatives(numbers):
    positive_numbers = []
    for number in numbers:
        if number >= 0:
            positive_numbers.append(number)
    return positive_numbers


def remove_positives(numbers):
    negative_numbers = []
    for number in numbers:
        if number < 0:
            negative_numbers.append(number)
    return negative_numbers


def get_high_from_candle_closes(replaced_percentage_difference, ohlc_list):
    result = replaced_percentage_difference
    for i in range(len(replaced_percentage_difference)):
        if replaced_percentage_difference[i] != 101:
            result[i] = ohlc_list[i][2]
    return result


def get_low_from_candle_closes(replaced_percentage_difference_list, ohlc_list):
    result = copy.deepcopy(replaced_percentage_difference_list)
    for i in range(len(result)):
        if result[i] != 101:
            result[i] = ohlc_list[i][3]
    return result


def get_standard_dev(list):
    if len(list) > 1:
        return statistics.stdev(list)
    else:
        return 9999999



def summary(bybit_url, threshold):
    # rules:
    # no.1 we only consider clusters where the closes are within a % range. Candle with god wicks will not be counted into a cluster. However candles with closes within the range and large wicks are counted.

    short_string = bybit_url.replace("https://api.cryptowat.ch/markets/bybit/","",1)
    print(short_string)

    # Get the data in all forms
    ohlc_data = get_price_history(
        bybit_url)

    # print("ema200 data:")
    ema200_data = get_200ema_list(ohlc_data)
    # print(ema200_data)

    # CLOSES
    # print("Difference in close price and 200ema")
    difference = get_difference_price_and_200ema(ohlc_data, ema200_data, 4)
    # print(difference)

    # print("percentage differences closes and 200ema")
    percentage_difference = get_percentage_difference_price(difference, ohlc_data, 4)
    # print(percentage_difference)

    # print("percentage differences closes and 200ema replaced with 101 if outside of threshold range")
    replaced_percentage_difference_closes = replace_percentage_price(threshold, percentage_difference)
    # print(replaced_percentage_difference_closes)
    replaced_percentage_difference_closes_2 = copy.deepcopy(replaced_percentage_difference_closes)

    # print("percentage difference closes and 200ema in one long list with the 101 removed")
    removed_replaced_values_closes = remove_replaced_percentage_price(replaced_percentage_difference_closes)
    # print(removed_replaced_values_closes)

    # HIGHS
    # print("HIGHS")
    # print("highs with candle closes below the threshold with 101 if outside of threshold range")
    price_highs_within_threshold = get_high_from_candle_closes(replaced_percentage_difference_closes_2, ohlc_data)
    # print(price_highs_within_threshold)

    # print("Difference in highs and 200ema, for closes below threshold with 101 if outside of threshold range")
    difference_highs = get_difference_price_and_200ema(ohlc_data, ema200_data, 2)
    # print(difference_highs)

    # print("percentage differences highs and 200ema, for closes below threshold with 101 if outside of threshold range")
    percentage_difference_highs = get_percentage_difference_price(difference_highs, ohlc_data, 2)
    # print(percentage_difference_highs)

    # print("percentage differences of highs and 200ema, replaced with 101 if outside of threshold range")
    replaced_percentage_difference_highs = replace_percentage_price(threshold, percentage_difference_highs)
    # print(replaced_percentage_difference_highs)

    # print("percentage difference of highs and 200ema, in one long list with the 101 removed")
    removed_replaced_values_highs = remove_replaced_percentage_price(replaced_percentage_difference_highs)
    # print(removed_replaced_values_highs)

    # LOWS
    # print("LOWS")
    # print("lows with candle closes below the threshold with 101 if outside of threshold range")
    price_lows_within_threshold = get_low_from_candle_closes(replaced_percentage_difference_closes_2, ohlc_data)
    # print(price_lows_within_threshold)

    # print("Difference in lows and 200ema, for closes below threshold with 101 if outside of threshold range")
    difference_lows = get_difference_price_and_200ema(ohlc_data, ema200_data, 3)
    # print(difference_lows)

    # print("percentage differences lows and 200ema, for closes below threshold with 101 if outside of threshold range")
    percentage_difference_lows = get_percentage_difference_price(difference_lows, ohlc_data, 3)
    # print(percentage_difference_lows)

    # print("percentage differences of lows and 200ema, replaced with 101 if outside of threshold range")
    replaced_percentage_difference_lows = replace_percentage_price(threshold, percentage_difference_lows)
    # print(replaced_percentage_difference_lows)

    # print("percentage difference of lows and 200ema, in one long list with the 101 removed")
    removed_replaced_values_lows = remove_replaced_percentage_price(replaced_percentage_difference_lows)
    # print(removed_replaced_values_lows)

    # CLUSTERS
    # print("CLUSTERS")
    # print("lists within a list of price clusters around the 4h200ema within the threshold")
    # print(replaced_percentage_difference_closes)
    clustered_price_difference_closes = create_array_of_array(replaced_percentage_difference_closes)
    # print(clustered_price_difference_closes)
    # print(replaced_percentage_difference_highs)
    clustered_price_difference_highs = create_array_of_array(replaced_percentage_difference_highs)
    print(clustered_price_difference_highs)
    # print(replaced_percentage_difference_lows)
    clustered_price_difference_lows = create_array_of_array(replaced_percentage_difference_lows)
    print(clustered_price_difference_lows)



    # so basically i've got the data for price differences above and below the 4h200ema when the price is within a 10% range of the 4h200ema
    print("Across all the local clusters of a " + str(threshold)+"% price range of the 4h200ema...")

    print("Average closing price (absolute value) around the 4h200ema:")
    # make all values absolute and average the values
    print(str(average_of_list(make_list_absolute(removed_replaced_values_closes))) + "%")

    print("Average closing price above 4h200ema:")  # this means you can easily get fill a short with an avg % above the 4h200ema, instead of filling on the 4h 200ema touches
    print(str(average_of_list(remove_negatives(removed_replaced_values_closes))) + "%")

    print("Average closing price below 4h200ema:")  # this means you can easily get fill a long with an avg % above the 4h200ema, instead of filling on the 4h 200ema touches
    print(str(average_of_list(remove_positives(removed_replaced_values_closes))) + "%")

    print("Average wick high above 4h200ema:")  # this means from past clusters around the 4h200ema, the average price never went % higher than the 4h200ema, on average if you place a stop loss at this % you won't get stopped out.
    print(str(average_of_list(remove_negatives(removed_replaced_values_highs))) + "%")

    print("Average wick low below 4h200ema:")  # this means from past clusters around the 4h200ema, the average price never went % lower than the 4h200ema, on average if you place a stop loss at this % you won't get stopped out.
    print(str(average_of_list(remove_positives(removed_replaced_values_lows))) + "%")

    print("Std dev (1,2,3) of closing price above 4h 200ema:")  # this means if you place a stop % above the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a close.
    above_stddev_closes = get_standard_dev(remove_negatives(removed_replaced_values_closes))
    print(str(above_stddev_closes), str(above_stddev_closes*2), str(above_stddev_closes*3))

    print("Std dev (1,2,3) of closing price below 4h 200ema:")  # this means if you place a stop % below the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a close.
    below_stddev_closes = get_standard_dev(remove_positives(removed_replaced_values_closes))
    print(str(below_stddev_closes), str(below_stddev_closes*2), str(below_stddev_closes*3))

    print("Std dev (1,2,3) of wick high price above 4h 200ema:")  # this means if you place a stop % above the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a wick.
    above_stddev_highs = get_standard_dev(remove_negatives(removed_replaced_values_highs))
    print(str(above_stddev_highs), str(above_stddev_highs * 2), str(above_stddev_highs * 3))

    print("Std dev (1,2,3) of wick low price below 4h 200ema:")  # this means if you place a stop % below the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a wick.
    above_stddev_lows = get_standard_dev(remove_negatives(removed_replaced_values_lows))
    print(str(above_stddev_lows), str(above_stddev_lows * 2), str(above_stddev_lows * 3))

    print("Analysing based on each local cluster:")
    print("Recent 10 local clusters high, low, average close around the 4h200ema")
    cluster_close_max = []
    cluster_close_min = []
    stddev_above = []
    stddev_below = []
    for i in range(-1, -11, -1):
        # print(i)
        try:
            cluster = clustered_price_difference_closes[i]
            # print(cluster)
            # print("cluster closes max", max(cluster))
            cluster_close_max.append(max(cluster))
            # print("cluster closes min", min(cluster))
            cluster_close_min.append(min(cluster))
        except IndexError:  # means there's less than 10 recent clusters
            break
        if len(remove_negatives(cluster)) > 1:
            # print("Std dev (1,2,3) of closing price above 4h 200ema:")  # this means if you place a stop % above the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a close.
            above_stddev_closes = get_standard_dev(remove_negatives(cluster))
            # print(str(above_stddev_closes), str(above_stddev_closes * 2), str(above_stddev_closes * 3))
            stddev_above.append([str(above_stddev_closes), str(above_stddev_closes * 2), str(above_stddev_closes * 3)])
        else:
            stddev_above.append(["none"])
        if len(remove_positives(cluster)) > 1:
            # print("Std dev (1,2,3) of closing price below 4h 200ema:")  # this means if you place a stop % below the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a close.
            below_stddev_closes = get_standard_dev(remove_positives(cluster))
            # print(str(below_stddev_closes), str(below_stddev_closes * 2), str(below_stddev_closes * 3))
            stddev_below.append([str(below_stddev_closes), str(below_stddev_closes * 2), str(below_stddev_closes * 3)])
        else:
            stddev_below.append(["none"])
    print("Recent 10 local clusters close highs:")
    print(cluster_close_max)
    print("Recent 10 local clusters close lows:")
    print(cluster_close_min)
    print("Recent 10 local clusters std dev (1,2,3) of closing price above 4h 200ema:")
    print(stddev_above)
    print("Recent 10 local clusters std dev (1,2,3) of closing price below 4h 200ema:")
    print(stddev_below)

    print("Recent 10 local clusters wick high, wick low, average close around the 4h200ema")
    cluster_high_max = []
    cluster_low_min = []
    stddev_high_above = []
    stddev_low_below = []
    for i in range(-1, -11, -1):
        # print(i)
        try:
            cluster_high = clustered_price_difference_highs[i]
            cluster_low = clustered_price_difference_lows[i]
            # print(cluster)
            # print("cluster closes max", max(cluster))
            cluster_high_max.append(max(cluster_high))
            # print("cluster closes min", min(cluster))
            cluster_low_min.append(min(cluster_low))
        except IndexError:  # means there's less than 10 recent clusters
            break

        if len(remove_negatives(cluster_high)) > 1:
            # print("Std dev (1,2,3) of closing price above 4h 200ema:")  # this means if you place a stop % above the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a close.
            above_stddev_closes = get_standard_dev(remove_negatives(cluster_high))
            # print(str(above_stddev_closes), str(above_stddev_closes * 2), str(above_stddev_closes * 3))
            stddev_high_above.append([str(above_stddev_closes), str(above_stddev_closes * 2), str(above_stddev_closes * 3)])
        else:
            stddev_high_above.append(["none"])
        if len(remove_positives(cluster_low)) > 1:
            # print("Std dev (1,2,3) of closing price below 4h 200ema:")  # this means if you place a stop % below the 4h200ema, you won't get stopped 68%, 95% or 99% of the time, on a close.
            below_stddev_closes = get_standard_dev(remove_positives(cluster_low))
            # print(str(below_stddev_closes), str(below_stddev_closes * 2), str(below_stddev_closes * 3))
            stddev_low_below.append([str(below_stddev_closes), str(below_stddev_closes * 2), str(below_stddev_closes * 3)])
        else:
            stddev_low_below.append(["none"])
    print("Recent 10 local clusters wick highs:")
    print(cluster_high_max)
    print("Recent 10 local clusters wick lows:")
    print(cluster_low_min)
    print("Recent 10 local clusters std dev (1,2,3) of wick high price above 4h 200ema:")
    print(stddev_high_above)
    print("Recent 10 local clusters std dev (1,2,3) of wick low price below 4h 200ema:")
    print(stddev_low_below)


if __name__ == '__main__':
    # pprint.pprint(get_bybit_usdt_perps())

    # print(get_bybit_usdt_perps())
    #
    # price_data = get_price_history("https://api.cryptowat.ch/markets/bybit/ethusdt-perpetual-futures/ohlc?periods=14400")
    # # print(price_data)
    # print(price_data[-1][4])
    #
    # ema200_data = get_200ema_list(price_data)
    # # print(list(reversed(ema200_data)))
    # print(ema200_data)
    #
    # difference = get_difference_price_and_200ema(price_data, ema200_data)
    # print(difference)
    #
    # percentage_difference = get_percentage_difference(difference, price_data)
    # print(percentage_difference)
    #
    # replaced_percentage_difference = replace_percentage_price(10, percentage_difference)
    # print(replaced_percentage_difference)
    #
    # removed_replaced_values = remove_replaced_percentage_price(replaced_percentage_difference)
    # print(removed_replaced_values)
    # print("standard deviation for all values less than 10, based on closing price")
    # std = statistics.stdev(removed_replaced_values)
    # print(std)

    # clustered_price_difference = create_array_of_array(replaced_percentage_difference)
    # print(clustered_price_difference)
    # print("standard deviations of clusters less than 10, based on closing price")
    # for i in clustered_price_difference:
    #     print(i)
    #     if len(i) > 1:
    #         std = statistics.stdev(i)
    #         print(std)

    # summary("https://api.cryptowat.ch/markets/bybit/ethusdt-perpetual-futures/ohlc?periods=14400", 10)
    # summary("https://api.cryptowat.ch/markets/bybit/1000luncusdt-perpetual-futures/ohlc?periods=14400", 7)
    summary("https://api.cryptowat.ch/markets/bybit/renusdt-perpetual-futures/ohlc?periods=14400", 10)
    # summary("https://api.cryptowat.ch/markets/okx/lunausdt-perpetual-futures/ohlc?periods=14400", 7)
