# Purpose:
# The purpose of this file is to add logic and rules to the DNA that are sent to the NFTRecord.json file in
# dna_generator.py

import random
import logging
import traceback
import collections

from .helpers import TextColors

log = logging.getLogger(__name__)


def reconstruct_dna(deconstructed_dna):
    reconstructed_dna = ""
    for a in deconstructed_dna:
        num = f"-{str(a)}"
        reconstructed_dna += num
    return ''.join(reconstructed_dna.split('-', 1))


def get_var_info(variant, hierarchy):
    # Get info for variant dict
    name = variant.split("_")[0]
    order_number = variant.split("_")[1]
    rarity_number = variant.split("_")[2]
    attribute = ""

    for a in hierarchy:
        for var in list(hierarchy[a].keys()):
            if var == variant:
                attribute = a
                break
    attribute_index = list(hierarchy.keys()).index(attribute)

    return [name, order_number, rarity_number, attribute, attribute_index]  # list of Var info sent back


def logic_rarity(variant_list, enable_rarity, a):
    number_list_of_i = []
    rarity_list_of_i = []
    if_zero_bool = None
    variant_num = None

    for b in variant_list:
        number = b.split("_")[1]
        rarity = b.split("_")[2]

        number_list_of_i.append(int(number))
        rarity_list_of_i.append(float(rarity))

    for b in rarity_list_of_i:
        if_zero_bool = b == 0
    if enable_rarity:
        try:
            if if_zero_bool:
                variant_num = random.choices(number_list_of_i, k=1)
            else:
                variant_num = random.choices(number_list_of_i, weights=rarity_list_of_i, k=1)
        except IndexError:
            log.error(
                f"\n{traceback.format_exc()}"
                f"\n{TextColors.ERROR}Blend_My_NFTs Error:\n"
                f"An issue was found within the Attribute collection '{a}'. For more information on "
                f"Blend_My_NFTs compatible scenes, see:\n{TextColors.RESET}"
                f"https://github.com/torrinworx/Blend_My_NFTs#blender-file-organization-and-structure\n"
            )
            raise IndexError()
    else:
        try:
            variant_num = random.choices(number_list_of_i, k=1)
        except IndexError:
            log.error(
                f"\n{traceback.format_exc()}"
                f"\n{TextColors.ERROR}Blend_My_NFTs Error:\n"
                f"An issue was found within the Attribute collection '{a}'. For more information on "
                f"Blend_My_NFTs compatible scenes, see:\n{TextColors.RESET}"
                f"https://github.com/torrinworx/Blend_My_NFTs#blender-file-organization-and-structure\n"
            )
            raise IndexError()
    return str(variant_num[0])


def apply_rule_to_dna(hierarchy, deconstructed_dna, if_dict, result_dict, result_dict_type, enable_rarity):
    """
    Applies a single given rule to the DNA. This function does not apply multiple rules at the same time.

    Then returns the new deconstructed_dna with the single rule applied to it.
    """

    # Check if Variants in if_dict are in deconstructed_dna, if so return if_list_selected = True:
    if_list_selected = False  # True if item in the if_dict (items in the IF dictionary of a rule) are selected
    for attribute_index, a in enumerate(deconstructed_dna):
        attribute = list(hierarchy.keys())[attribute_index]

        for b in hierarchy[attribute]:
            if hierarchy[attribute][b]["number"] == a and attribute in if_dict:
                a_dna_var = b

                if a_dna_var in list(if_dict[attribute].keys()):
                    if_list_selected = True
                    break

                continue

    # If Variants in if_dict are selected, select random or rarity variants or set the to Empty depending on the rule.
    if result_dict_type == "NOT":
        for a in result_dict:  # For each Attribute in the NOT rule dictionary
            attribute_index = list(hierarchy.keys()).index(a)
            attribute = list(hierarchy.keys())[attribute_index]
            full_att = list(result_dict[attribute].keys()) == list(
                hierarchy[attribute].keys())  # True if full attribute in rules

            if if_list_selected:
                # If 'a' is a full Attribute and Variants in if_dict selected, set 'a' to empty (0):
                if full_att:
                    deconstructed_dna[attribute_index] = "0"

                    # Not a full Attribute, invert the variants selected so that we get a list
                    # of just variants that can be selected. Because the NOT variants are what we don't want selected:
                if not full_att:
                    var_selected_list = list(result_dict[a].keys())  # list of variants from 'NOT'
                    att_selected_list = list(hierarchy[a].keys())  # full list of variants from hierarchy attribute

                    # Invert Variants set in NOT rule:
                    var_selected_list = [i for i in att_selected_list if i not in var_selected_list]

                    var_selected_list_complete = {
                        i: get_var_info(i, hierarchy)
                        for i in var_selected_list
                    }
                    result_dict[a] = var_selected_list_complete

                    # Select random or rarity from new result_dict with inverted variants if attribute is not full
                    variant_list = list(result_dict[a].keys())
                    deconstructed_dna[attribute_index] = logic_rarity(
                        variant_list, enable_rarity, a
                    )

    else:  # if result_dict_type == "THEN" basically
        for a in result_dict:
            attribute_index = list(hierarchy.keys()).index(a)
            attribute = list(hierarchy.keys())[attribute_index]
            full_att = list(result_dict[attribute].keys()) == list(
                hierarchy[attribute].keys())  # True if full attribute in rules

            variant_list = list(result_dict[a].keys())

            # If 'a' is a full Attribute and Variants in if_dict are not selected, set 'a' to empty (0):
            # This makes it so Attributes specified in THEN rules will only appear when a given Variant in if_dict is selected.
            # if full_att and not if_list_selected:
            #     deconstructed_dna[attribute_index] = "0"

            # If Variants in if_dict selected, regardless if they make a full variant, select items from result_dict
            if if_list_selected:
                deconstructed_dna[attribute_index] = logic_rarity(
                    variant_list, enable_rarity, a
                )

    return deconstructed_dna


def get_rule_break_type(hierarchy, deconstructed_dna, if_dict, result_dict, result_dict_type):
    """
    Checks if a given rule has been broken by deconstructed_dna.
    """
    # Check if Variants in 'if_dict' found in deconstructed_dna:
    if_bool = False  # True if Variant in 'deconstructed_dna' found in 'if_dict'
    for a in if_dict:  # Attribute in 'if_dict'
        for b in if_dict[a]:  # Variant in if_dict[Attribute]
            var_order_num = str(if_dict[a][b][1])  # Order number of 'b' (Variant)
            dna_order_num = str(
                deconstructed_dna[if_dict[a][b][4]])  # Order Number of 'b's attribute in deconstructed_dna

            if var_order_num == dna_order_num:  # If DNA selected Variants found inside IF list variants:
                if_bool = True
                break
        else:
            continue
        break

    # Check if Variants in 'result_dict' found in deconstructed_dna:
    full_att_bool = False
    result_bool = False  # True if Variant in 'deconstructed_dna' found in 'result_dict'
    then_bool = False
    for a in result_dict:  # Attribute in 'result_dict'
        for b in result_dict[a]:  # Variant in if_dict[Attribute]
            var_order_num = str(result_dict[a][b][1])  # Order number of 'b' (Variant)
            dna_order_num = str(
                deconstructed_dna[result_dict[a][b][4]])  # Order Number of 'b's attribute in deconstructed_dna
            if var_order_num == dna_order_num:  # If DNA selected Variants found inside THEN list variants:
                if list(result_dict[a].keys()) == list(hierarchy[a].keys()):
                    full_att_bool = True
                result_bool = True
                # break
            else:
                then_bool = True
        else:
            continue
        break

    violates_rule = bool(
        if_bool
        and then_bool
        or if_bool
        and result_bool
        and result_dict_type == "NOT"
        or not if_bool
        and result_bool
        and full_att_bool
    )
    # If Variants in 'if_dict' not found in deconstructed_dna, but Variants in 'then_dict' are found in
    # deconstructed_dna, and don't make up a full Attribute:
    # elif not if_bool and result_bool and not full_att_bool:
    #     violates_rule = False

    return violates_rule, if_bool, result_bool, full_att_bool


def create_dicts(hierarchy, rule_list_items, result_dict_type):
    """
    Example of output structure:

    structure = {
        "attribute1": {
            "variant1": [
                "name",
                "order_number",
                "rarity_number"
                "attribute"
                "attribute_index"
            ],
            "variant2": [
                "name",
                "order_number",
                "rarity_number"
                "attribute"
                "attribute_index"
            ]
        },
        "attribute2": {
            "variant1": [
                "name",
                "order_number",
                "rarity_number"
                "attribute"
                "attribute_index"
            ],
            "variant2": [
                "name",
                "order_number",
                "rarity_number"
                "attribute"
                "attribute_index"
            ]
        }
    }
    """

    items_returned = collections.defaultdict(dict)
    for a in rule_list_items:
        for b in hierarchy:
            if a == b:  # If 'a' is an Attribute, add all 'a' Variants to items_returned dict.
                variant_list_of_a = list(hierarchy[a].keys())
                variant_dict_of_a = {c: get_var_info(c, hierarchy) for c in variant_list_of_a}
                items_returned[a] = variant_dict_of_a

            if a in list(hierarchy[b].keys()):  # If 'a' is a Variant, add all info about that variant to items_returned
                items_returned[b][a] = get_var_info(a, hierarchy)

    items_returned = dict(items_returned)

    return dict(items_returned)


def logicafy_dna_single(hierarchy, single_dna, logic_file, enable_rarity):
    deconstructed_dna = single_dna.split("-")
    did_reconstruct = True
    original_dna = str(single_dna)

    while did_reconstruct:
        did_reconstruct = False
        for rule in logic_file:
            # Items from 'IF' key for a given rule
            if_dict = create_dicts(hierarchy, logic_file[rule]["IF"], "IF")

            # TODO: This needs to be made more efficient with less repeating code, but it works I guess:
            if "THEN" in logic_file[rule]:
                result_dict_type = "THEN"
                result_dict = create_dicts(hierarchy, logic_file[rule][result_dict_type], result_dict_type)

                # Change 'then_bool' to 'result_bool'
                violates_rule, if_bool, then_bool, full_att_bool = get_rule_break_type(
                    hierarchy,
                    deconstructed_dna,
                    if_dict,
                    result_dict,
                    result_dict_type,
                )

                # Check THEN rule again but swap IF and THEN dicts.
                if not violates_rule:
                    violates_rule, if_bool, then_bool, full_att_bool = get_rule_break_type(
                        hierarchy,
                        deconstructed_dna,
                        result_dict,
                        if_dict,
                        result_dict_type,
                    )

                if violates_rule:
                    log.debug(f"======={deconstructed_dna} VIOLATES RULE======")

                    deconstructed_dna = apply_rule_to_dna(
                        hierarchy,
                        deconstructed_dna,
                        if_dict,
                        result_dict,
                        result_dict_type,
                        enable_rarity
                    )

                    new_dna = reconstruct_dna(deconstructed_dna)
                    if new_dna != original_dna:
                        original_dna = str(new_dna)
                        did_reconstruct = True
                        break
            # TODO: This needs to be made more efficient with less repeating code, but it works I guess:
            if "NOT" in logic_file[rule]:
                result_dict_type = "NOT"
                result_dict = create_dicts(hierarchy, logic_file[rule][result_dict_type], result_dict_type)

                # Change 'then_bool' to 'result_bool'
                violates_rule, if_bool, then_bool, full_att_bool = get_rule_break_type(
                    hierarchy,
                    deconstructed_dna,
                    if_dict,
                    result_dict,
                    result_dict_type,
                )

                # Check NOT rule again but swap IF and NOT dicts.
                if not violates_rule:
                    violates_rule, if_bool, then_bool, full_att_bool = get_rule_break_type(
                        hierarchy,
                        deconstructed_dna,
                        result_dict,
                        if_dict,
                        result_dict_type,
                    )

                if violates_rule:
                    log.debug(f"======={deconstructed_dna} VIOLATES RULE======")

                    deconstructed_dna = apply_rule_to_dna(
                        hierarchy,
                        deconstructed_dna,
                        if_dict,
                        result_dict,
                        result_dict_type,
                        enable_rarity
                    )

                    new_dna = reconstruct_dna(deconstructed_dna)
                    if new_dna != original_dna:
                        original_dna = str(new_dna)
                        did_reconstruct = True
                        break

    return str(reconstruct_dna(deconstructed_dna))
