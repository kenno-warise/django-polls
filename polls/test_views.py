import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Question


def create_question(question_text, days):
    """
    Create a question with given 'question_text' and published the
    given number of 'days' offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


# ビューのテスト
class QuestionIndexViewTests(TestCase):
    def test_no_question(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])
        
    def test_past_question_no_choice(self):
        """
        過去の質問に対しても選択肢の無い質問は表示されない。
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_choice_in_past_question(self):
        """
        過去の質問に対して選択肢のある質問は表示する。
        """
        question = create_question(question_text="Past question.", days=-30)
        question.choice_set.create(choice_text="Past choice 1.", votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
                response.context['latest_question_list'],
                [question],
        )

    def test_choice_in_future_question(self):
        """
        Question with a pub_date in the future aren't displayed on the index page.
        """
        create_question(question_text="Future question.", days=30).choice_set.create(choice_text="Futer choice 1.", votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_choice_in_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions are displayed.
        """
        question = create_question(question_text="Past question.", days=-30)
        question.choice_set.create(choice_text="Past choice 1.", votes=0)
        create_question(question_text="Future question.", days=30).choice_set.create(choice_text="Futer choice 1.", votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
                response.context['latest_question_list'],
                [question],
        )

    def test_tow_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        question1.choice_set.create(choice_text="Past choice 1.", votes=0)
        question2.choice_set.create(choice_text="Past choice 1.", votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
                response.context['latest_question_list'],
                [question2, question1],
        )

    def test_authenticated_future_question_and_past_question(self):
        """
        認証済みの場合は過去未来選択肢無しの質問全てを表示する。
        """
        question1 = create_question(question_text="Past question.", days=-30)
        question2 = create_question(question_text="Future question.", days=30)
        self.client.force_login(User.objects.create_user('tester'))
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
                response.context['latest_question_list'],
                [question2, question1],
        )


    def test_no_authenticated_future_question_and_past_question(self):
        """
        認証されていない非公開質問は表示されない。
        """
        question1 = create_question(question_text="Past question.", days=-30)
        question2 = create_question(question_text="Future question.", days=30)
        self.client.logout()
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])


# 詳細のテスト
class QuestionDetailViewTests(TestCase):
    def test_detail_choice_in_future_question(self):
        """
        The detail view of a question with a pub_date in the future returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        future_question.choice_set.create(choice_text="Future choice 1.", votes=0)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_past_question_no_choice(self):
        """
        過去の質問に対しても選択肢がなければ詳細ページでは表示しない。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_choice_in_past_question(self):
        """
        過去の質問に対して選択肢があれば詳細ページに表示される。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        past_question.choice_set.create(choice_text="Past choice 1.", votes=0)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_authenticated_detail_past_question_no_choice(self):
        """
        認証済みの過去の質問に対しても選択肢がなくても詳細ページで表示する。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        self.client.force_login(User.objects.create_user('tester'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

# 結果のテスト
class QuestionLesultsViewTests(TestCase):
    def test_results_choice_in_future_question(self):
        """
        未来の質問且つ選択肢のある質問の結果は404エラーにする。
        """
        future_question = create_question(question_text='Future question.', days=5)
        future_question.choice_set.create(choice_text="Future choice 1.", votes=0)
        url = reverse('polls:results', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_results_past_question_no_choice(self):
        """
        過去の質問に対して選択肢のない質問の結果は404エラーにする。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_results_choice_in_past_questioni(self):
        """
        過去の質問且つ選択肢のある質問の結果はテキストを表示する。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        past_question.choice_set.create(choice_text="Past choice 1.", votes=0)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_authenticated_results_past_question_no_choice(self):
        """
        認証済みの場合は過去の質問に対して選択肢のない質問の結果は表示する。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:results', args=(past_question.id,))
        self.client.force_login(User.objects.create_user('tester'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


# 選択のテスト
class QuestionVoteViewTests(TestCase):
    def test_vote_choice_in_future_question(self):
        """
        未来の質問且つ選択肢のある質問の投票では404エラーとする。
        """
        future_question = create_question(question_text='Future question.', days=5)
        future_question.choice_set.create(choice_text="Future choice 1.", votes=0)
        url = reverse('polls:vote', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_vote_past_question_no_choice(self):
        """
        過去の質問に対して選択肢のない投票は404エラーとする。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:vote', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_vote_choice_in_past_question(self):
        """
        過去の質問且つ選択肢のある投票はテキストを表示する。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        past_question.choice_set.create(choice_text="Past choice 1.", votes=0)
        url = reverse('polls:vote', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_authenticated_vote_past_question_no_choice(self):
        """
        認証済みの場合は過去の質問に対して選択肢のない投票は表示する。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:vote', args=(past_question.id,))
        self.client.force_login(User.objects.create_user('tester'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_choice_and_vote(self):
        """
        質問の選択肢を選択して投票した結果。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        past_choice = past_question.choice_set.create(choice_text="Past choice 1.", votes=0)
        url = reverse('polls:vote', args=(past_question.id,))
        response = self.client.post(url, {'choice':1})
        self.assertRedirects(response, '/1/results/', msg_prefix='リダイレクト先URLが違う')

    def test_vote_without_choice(self):
        """
        質問の選択肢を選択せずに投票した結果。
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        past_question.choice_set.create(choice_text="Past choice 1.", votes=0)
        url = reverse('polls:vote', args=(past_question.id,))
        response = self.client.post(url, {'choice':0})
        self.assertContains(response, past_question.question_text)

