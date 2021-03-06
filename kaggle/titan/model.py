if __name__ == '__main__':

    import pandas as pd  # 数据分析
    import numpy as np  # 科学计算
    from pandas import Series, DataFrame
    import matplotlib.pyplot as plt
    import sklearn.preprocessing as preprocessing
    from sklearn import linear_model
    from sklearn import svm
    from sklearn import model_selection
    from sklearn.ensemble import BaggingRegressor

    data_train = pd.read_csv("train.csv")

    from sklearn.ensemble import RandomForestRegressor


    ### 使用 RandomForestClassifier 填补缺失的年龄属性
    def set_missing_ages(df):
        # 把已有的数值型特征取出来丢进Random Forest Regressor中
        age_df = df[['Age', 'Fare', 'Parch', 'SibSp', 'Pclass']]  # df 是 dataFrame类型的

        # 乘客分成已知年龄和未知年龄两部分
        known_age = age_df[age_df.Age.notnull()].as_matrix()
        unknown_age = age_df[age_df.Age.isnull()].as_matrix()

        # y即目标年龄
        y = known_age[:, 0]  #:代表全部行，0代表第一列

        # X即特征属性值
        X = known_age[:, 1:]  # 全部行，第二列开始？

        # fit到RandomForestRegressor之中
        rfr = RandomForestRegressor(random_state=0, n_estimators=2000, n_jobs=-1)
        rfr.fit(X, y)

        # 用得到的模型进行未知年龄结果预测
        predictedAges = rfr.predict(unknown_age[:, 1::])

        # 用得到的预测结果填补原缺失数据
        df.loc[(df.Age.isnull()), 'Age'] = predictedAges

        return df, rfr


    def set_Cabin_type(df):
        df.loc[(df.Cabin.notnull()), 'Cabin'] = "Yes"
        df.loc[(df.Cabin.isnull()), 'Cabin'] = "No"
        return df


    data_train, rfr = set_missing_ages(data_train)
    data_train = set_Cabin_type(data_train)

    dummies_Cabin = pd.get_dummies(data_train['Cabin'], prefix='Cabin')

    dummies_Embarked = pd.get_dummies(data_train['Embarked'], prefix='Embarked')

    dummies_Sex = pd.get_dummies(data_train['Sex'], prefix='Sex')

    dummies_Pclass = pd.get_dummies(data_train['Pclass'], prefix='Pclass')

    df = pd.concat([data_train, dummies_Cabin, dummies_Embarked, dummies_Sex, dummies_Pclass], axis=1)
    df.drop(['Pclass', 'Name', 'Sex', 'Ticket', 'Cabin', 'Embarked'], axis=1, inplace=True)

    scaler = preprocessing.StandardScaler()

    age_scale_param = scaler.fit(df['Age'].values.reshape(-1, 1))
    df['Age_scaled'] = scaler.fit_transform(df['Age'].values.reshape(-1, 1), age_scale_param)
    fare_scale_param = scaler.fit(df['Fare'].values.reshape(-1, 1))
    df['Fare_scaled'] = scaler.fit_transform(df['Fare'].values.reshape(-1, 1), fare_scale_param)

    # 用正则取出我们要的属性值
    train_df = df.filter(regex='Survived|Age_.*|SibSp|Parch|Fare_.*|Cabin_.*|Embarked_.*|Sex_.*|Pclass_.*')
    train_np = train_df.as_matrix()

    # y即Survival结果
    y = train_np[:, 0]

    # X即特征属性值
    X = train_np[:, 1:]

    # 分割数据，按照 训练数据:cv数据 = 7:3的比例
    split_train, split_cv = model_selection.train_test_split(df, test_size=0.3, random_state=0)
    train_df = split_train.filter(regex='Survived|Age_.*|SibSp|Parch|Fare_.*|Cabin_.*|Embarked_.*|Sex_.*|Pclass_.*')

    # fit到BaggingRegressor之中
    clf = linear_model.LogisticRegression(C=1.0, penalty='l1', tol=1e-6)
    clf = BaggingRegressor(clf, n_estimators=20, max_samples=0.8, max_features=1.0, bootstrap=True,
                           bootstrap_features=False, n_jobs=-1)
    clf.fit(X, y)

    cv_df = split_cv.filter(regex='Survived|Age_.*|SibSp|Parch|Fare_.*|Cabin_.*|Embarked_.*|Sex_.*|Pclass_.*')
    predictions = clf.predict(cv_df.as_matrix()[:, 1:])

    # bad_cases = data_train.loc[data_train['PassengerId'].isin(split_cv[predictions != cv_df.as_matrix()[:,0]]['PassengerId'].values)]

    data_test = pd.read_csv("test.csv")
    # 均值
    data_test.loc[(data_test.Fare.isnull()), 'Fare'] = data_test.loc[(data_test.Age.notnull()), 'Age'].mean()
    # 接着我们对test_data做和train_data中一致的特征变换
    # 首先用同样的RandomForestRegressor模型填上丢失的年龄
    tmp_df = data_test[['Age', 'Fare', 'Parch', 'SibSp', 'Pclass']]
    null_age = tmp_df[data_test.Age.isnull()].as_matrix()
    # 根据特征属性X预测年龄并补上
    X = null_age[:, 1:]
    predictedAges = rfr.predict(X)
    data_test.loc[(data_test.Age.isnull()), 'Age'] = predictedAges

    data_test = set_Cabin_type(data_test)
    dummies_Cabin = pd.get_dummies(data_test['Cabin'], prefix='Cabin')
    dummies_Embarked = pd.get_dummies(data_test['Embarked'], prefix='Embarked')
    dummies_Sex = pd.get_dummies(data_test['Sex'], prefix='Sex')
    dummies_Pclass = pd.get_dummies(data_test['Pclass'], prefix='Pclass')

    df_test = pd.concat([data_test, dummies_Cabin, dummies_Embarked, dummies_Sex, dummies_Pclass], axis=1)
    df_test.drop(['Pclass', 'Name', 'Sex', 'Ticket', 'Cabin', 'Embarked'], axis=1, inplace=True)
    df_test['Age_scaled'] = scaler.fit_transform(df_test['Age'].values.reshape(-1, 1), age_scale_param)
    df_test['Fare_scaled'] = scaler.fit_transform(df_test['Fare'].values.reshape(-1, 1), fare_scale_param)

    test = df_test.filter(regex='Age_.*|SibSp|Parch|Fare_.*|Cabin_.*|Embarked_.*|Sex_.*|Pclass_.*')
    predictions = clf.predict(test)
    result = pd.DataFrame({'PassengerId': data_test['PassengerId'].as_matrix(), 'Survived': predictions.astype(np.int32)})
    result.to_csv("logistic_regression_predictions.csv", index=False)
