#!/usr/bin/env python

import argparse
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--states', nargs='+', default=[])
    parser.add_argument("--subsample", type=int, default=None, help="Subsample-training data")
    args = parser.parse_args()
    data_path = "data/raw/CES22_Common.csv"
    df = pd.read_csv(data_path)
    states = pd.read_csv("data/raw/states.csv").States

    # This maps will be used for renaming columns.
    cols = {
        "inputzip":"zipcode",
        "cit1": "US_citizen",
        "votereg": "registered_to_vote",
        "inputstate": "state",
        "birthyr": "age",
        "gender4": "gender",
        "educ": "education",
        "race": "race",
        "religpew": "religion",
        "union": "union_member",
        "CC22_401": "did_you_vote",
        "CC22_403": "how_did_you_vote",
        "CC22_403c": "where_was_ballot_returned",
        "CC22_406a": "problem_voting",
        "CC22_415c": "state_senate_vote",
        "CC22_415d": "lower_chamber_vote",
        "CC22_403d": "waiting_for_voting",
        "comptype": "device_used",
        "pid3": "party_allegiance",
        "CC22_300_1": "used_social_media_in_past_24hrs",
        "CC22_300_2": "watched_tv_news_in_past_24hrs",
        "CC22_300_3": "read_newspaper_in_past_24hrs",
        "CC22_300_4": "listened_to_radio_news_in_past_24hrs",
        "CC22_302": "national_econony_has",
        "CC22_303": "my_house_income_has",
        "CC22_304": "prices_have",
        "CC22_305_1":  "married_last_year",
        "CC22_305_2":  "lost_job_last_year",
        "CC22_305_3":  "finished_school_last_year",
        "CC22_305_4":  "retired_last_year",
        "CC22_305_5":  "divorced_last_year",
        "CC22_305_6":  "had_a_child_last_year",
        "CC22_305_7":  "taken_new_job_last_year",
        "CC22_305_9":  "been_victim_of_crime_last_year",
        "CC22_305_10": "visited_emergency_room_last_year",
        "CC22_305_11": "visited_doctor_for_regular_examination_last_year",
        "CC22_305_12": "received_a_raise_last_year",
        "CC22_305_13": "jad_pay_cut_last_year",
        "CC22_307": "police_makes_me_feel",
        "CC22_309a_1": "I_had_COVID_last_year",
        "CC22_309a_2": "family_member_had_COVID_last_year",
        "CC22_309a_3": "friend_had_COVID_last_year",
        "CC22_309a_4": "co_worker_had_COVID_last_year",
        "CC22_306": "vaccination_status",
        "CC22_309c_1":  "pandemic_work_hours_reduced",
        "CC22_309c_2":  "pandemic_work_hours_restored",
        "CC22_309c_3":  "pandemic_temporarily_laid_off",
        "CC22_309c_4":  "pandemic_re_hired_after_temporarily_laid_off",
        "CC22_309c_5":  "pandemic_multiple_jobs_lost_one",
        "CC22_309c_8":  "pandemic_hours_increased",
        "CC22_309c_9":  "pandemic_take_additional_jobs",
        "CC22_309dx_1": "pay_for_emergency_with_credit_card_pay_off_next_statement",
        "CC22_309dx_2": "pay_for_emergency_with_credit_card_pay_off_over_time",
        "CC22_309dx_3": "pay_for_emergency_with_money_in_credit_savings_account",
        "CC22_309dx_4": "pay_for_emergency_with_bank_loan",
        "CC22_309dx_5": "pay_for_emergency_by_borrowing_from_friends_or_family",
        "CC22_309dx_6": "pay_for_emergency_with_advance_or_overdraft",
        "CC22_309dx_7": "pay_for_emergency_by_sell_something",
        "CC22_309e": "health_status",
        "CC22_309e": "mental_health_status",
        "CC22_310a": "which_party_has_majority_house",
        "CC22_310b": "which_party_has_majority_senate",
        "CC22_310c": "which_party_has_majority_in_my_state_senate",
        "CC22_310d": "which_party_has_majority_in_my_state_lower_chamber",
        "CC22_320a": "apporoval_president",
        "CC22_320b": "apporoval_congress",
        "CC22_320c": "apporoval_governor",
        "CC22_320d": "apporoval_state_legislature",
        "CC22_320e": "apporoval_my_current_member_congress",
        "CC22_320f": "apporoval_my_current_first_senator",
        "CC22_320f": "apporoval_my_current_second_senator",
        "CC22_327a": "policy_support_expanding_medicare",
        "CC22_327b": "policy_support_government_negotiate_with_drug_companies",
        "CC22_327c": "policy_support_repealing_ACA",
        "CC22_327d": "policy_support_allow_states_import_drugs_from_other_countries",
        "CC22_330a": "policy_support_prohibiting_states_publishing_names_of_gun_owners",
        "CC22_330b": "policy_support_ban_assault_rifles",
        "CC22_330c": "policy_support_easier_to_get_concealed_carry_permit",
        "CC22_330d": "policy_support_take_guns_away_from_people_who_pose_threat",
        "CC22_330e": "policy_support_background_checks_guns",
        "CC22_330f": "policy_support_allowing_teachers_to_carry_guns",
        "CC22_331a": "policy_support_grant_legal_status_if_working_for_3_years",
        "CC22_331b": "policy_support_increase_border_patrol",
        "CC22_331c": "policy_support_eliminate_visa_lottery_and_family_based_immigration",
        "CC22_331d": "policy_support_increase_spending_on_border_security_25_billions_and_build_wall",
        "CC22_332a": "policy_support_always_allow_abortion",
        "CC22_332b": "policy_support_permit_abortion_only_in_emergency",
        "CC22_332c": "policy_support_prohbit_all_abortions_after_week_20",
        "CC22_332d": "policy_support_allow_employers_deny_abortion_coverage",
        "CC22_332e": "policy_support_prohibit_federal_funds_be_used_for_abortion",
        "CC22_332f": "policy_support_make_all_abortions_illegal",
    }

    # Next, we define a few categorical mappings.
    yn = {1: "yes", 2: "no"}
    state_elections = {
        1: "Democratic",
        2: "Republican",
        3: "Other",
        4: "Did not vote in this race",
        5:  "There was no race for this office"
    }
    education =  {
            1:"(a) no high school degree",
            2:"(b) high school",
            3:"(c) college, no degree",
            4:"(d) 2-year college",
            5:"(e) 4-year college",
            6:"(f) Post graduate"}
    race =  {1:"White", 2:"Black", 3:"Latino", 4:"Asian", 5:"Native American", 8:"Middle Eastern", 6:"two or more", 7:"other"}
    incdec = {
            1: "(a) Increased a lot",
            2: "(b) Increased somewhat",
            3: "(c) Stayed about the same",
            4: "(e) Decreased somewhat",
            5: "(f) Decreased a lot",
        }
    exc_poor =  {
        1: "(a) Excellent",
        2: "(b) Very good",
        3: "(c) Good",
        4: "(d) Fair",
        5: "(e) Poor",
    }
    rep_dems = {
        1: "Republicans",
        2: "Democrats",
        3: "neither",
        4: "not sure",
    }
    approval = {
        1: "(a) strongly approve",
        2: "(b) somewhat approve",
        5: "(c) not sure",
        3: "(d) somewhat disapprove",
        4: "(e) strongly disapprove",
    }
    religions =  {
                1:  "Protestant",
                2:  "Roman Catholic",
                3:  "Mormon",
                4:  "Eastern or Greek Orthodox",
                5:  "Jewish",
                6:  "Muslim",
                7:  "Buddhist",
                8:  "Hindu",
                9:  "Atheist",
                10: "Agnostic",
                11: "Nothing in particular",
        }
    def saveint(v):
        if not np.isnan(v):
            return int(v)
    # The followoing dict defines how we convert categoricals. 
    convert_categoricals = {
        "inputzip": saveint,
        "cit1": yn,
        "votereg": {1:"yes", 2: "no", 3:None},
         "inputstate":{i+1:s for i,s in enumerate(states)},
         "birthyr": lambda x: 2023-x,
         "gender4":{1:"male", 2: "female", 3:"non-binary", 4:"other"},
         "educ": education,
         "race": race,
         "religpew": religions,
         "union": {1: "yes", 2: "formerly", 3: "no, never"},
         "CC22_401":{
            1: "(a) I did not vote in the election this November",
            2: "(b) I thought about voting this time – but didn't",
            3: "(c) I usually vote, but didn't this time",
            4: "(d) I attempted to vote but did not or could not",
            5: "(e) I definitely voted in the November 2022 General Election"
        },
        "CC22_403": {1: "in person, on election day", 2: "in person, before election day", 3: "mail", 4: "don't know"},
        "CC22_403c":{
            1: "Post office box at a U.S. Postal Service location",
            2: "Official post office box not at a U.S. Postal Service location",
            3: "Picked up by the postal worker who delivers mail to my home",
            4: "Drop box used only for ballots, not located at an election office or polling place",
            5: "Main election office",
            6: "Neighborhood polling place",
            7: "Voting center, not a neighborhood polling place",
            8: "Other",
            9: "I don’t know",
        },
        "CC22_403d":{
            1: "(a) Not at all",
            2: "(b) Less than 10 minutes",
            3: "(c) 10-30 minutes",
            4: "(d) 31 minutes – 1 hour",
            5: "(e) More than 1 hour",
            9: "(f) I don’t know",
        },
        "CC22_406a": {1: "no", 2: "yes"},
        "CC22_415c":state_elections,
        "CC22_415d":state_elections,
        "comptype": {1: "phone", 2: "tablet", 3: "computer"},
        "pid3": {1: "Democrat", 2: "Repulican", 3: "independent", 4: "other", 5: "not sure"},
        "CC22_300_1": yn,
        "CC22_300_2": yn,
        "CC22_300_3": yn,
        "CC22_300_4": yn,
        "CC22_302": {
            1: "(a) Gotten much better",
            2: "(b) Gotten somewhat better",
            3: "(c) Stayed about the same",
            4: "(d) Gotten somewhat worse",
            5: "(e) Gotten much worse",
        },
        "CC22_303": incdec,
        "CC22_304": incdec,
        "CC22_305_1":  yn,
        "CC22_305_2":  yn,
        "CC22_305_3":  yn,
        "CC22_305_4":  yn,
        "CC22_305_5":  yn,
        "CC22_305_6":  yn,
        "CC22_305_7":  yn,
        "CC22_305_9":  yn,
        "CC22_305_10": yn,
        "CC22_305_11": yn,
        "CC22_305_12": yn,
        "CC22_305_13": yn,
        "CC22_307": {
            1: "(a) Mostly safe",
            2: "(b) Somewhat safe",
            3: "(c) Somewhat unsafe",
            4: "(d) Mostly unsafe",
        },
        "CC22_309a_1": yn,
        "CC22_309a_2": yn,
        "CC22_309a_3": yn,
        "CC22_309a_4": yn,
        "CC22_306": {
            1: "(a) fully vaccinated and have received at least one booster shot",
            2: "(b) fully vaccinated but have not received a booster shot",
            3: "(c) partially vaccinated",
            4: "(d) not vaccinated at all",
        },
        "CC22_309c_1": yn,
        "CC22_309c_2": yn,
        "CC22_309c_3": yn,
        "CC22_309c_4": yn,
        "CC22_309c_5": yn,
        "CC22_309c_8": yn,
        "CC22_309c_9": yn,
        "CC22_309dx_1": yn,
        "CC22_309dx_2": yn,
        "CC22_309dx_3": yn,
        "CC22_309dx_4": yn,
        "CC22_309dx_5": yn,
        "CC22_309dx_6": yn,
        "CC22_309dx_7": yn,
        "CC22_309e": exc_poor,
        "CC22_309e": exc_poor,
        "CC22_310a": rep_dems,
        "CC22_310b": rep_dems,
        "CC22_310c": rep_dems,
        "CC22_310d": rep_dems,
        "CC22_320a": approval,
        "CC22_320b": approval,
        "CC22_320c": approval,
        "CC22_320d": approval,
        "CC22_320e": approval,
        "CC22_320f": approval,
        "CC22_327a": yn,
        "CC22_327b": yn,
        "CC22_327c": yn,
        "CC22_327d": yn,
        "CC22_330a": yn,
        "CC22_330b": yn,
        "CC22_330c": yn,
        "CC22_330d": yn,
        "CC22_330e": yn,
        "CC22_330f": yn,
        "CC22_331a": yn,
        "CC22_331b": yn,
        "CC22_331c": yn,
        "CC22_331d": yn,
        "CC22_332a": yn,
        "CC22_332b": yn,
        "CC22_332c": yn,
        "CC22_332d": yn,
        "CC22_332e": yn,
        "CC22_332f": yn,
    }
    # Run the conversion.
    for k,v in convert_categoricals.items():
        if isinstance(v, dict):
            df[k] = df[k].replace(v)
        else:
            df[k] = df[k].apply(v)
    df.rename(columns=cols, inplace=True)
    # Save to disk.
    df_training = df[~df.state.isin(args.states)]
    df_test = df[df.state.isin(args.states)]
    if args.subsample > 0:
        print(f"==== Subsample {args.subsample} training rows ===")
        out = df_training[cols.values()].sample(args.subsample, random_state=42)
        print(f"Number of rows in training data: {args.subsample}")
    else:
        out = df_training[cols.values()]
        print(f"Number of rows in training data: {out.shape[0]}")

    out.to_csv("data/data.csv", index=False)
    df_test[cols.values()].to_csv("data/test.csv", index=False)

    print(f"Number of rows in test data: {df_test.shape[0]}")
    # Load original dataframe and save:
    original_df = pd.read_csv(data_path)
    original_df = original_df.rename(columns=cols)[cols.values()]

    original_df.loc[out.index].to_csv("data/data-orig.csv", index=False)
    original_df.loc[df_test.index].to_csv("data/test-orig.csv", index=False)

if __name__ == "__main__":
    main()
